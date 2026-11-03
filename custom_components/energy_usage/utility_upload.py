# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Project Contributors
"""Authenticated, bounded upload of Green Button XML into Energy Ingest.

No utility credentials or XML files are persisted in Home Assistant.
"""

import asyncio
import base64
import binascii
import json
import logging

from homeassistant.components.http import HomeAssistantView
from homeassistant.const import CONF_URL
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from aiohttp import web

from .api import EnergyApi, EnergyApiError, EnergyAuthError
from .const import CONF_TOKEN, DOMAIN
from .statistics_sync_service import runtime_for_entry, sync_one

_LOGGER = logging.getLogger(__name__)
MAX_XML_BYTES = 8 * 1024 * 1024


class UtilityUploadView(HomeAssistantView):
    """Require Home Assistant authentication for every XML upload."""

    url = "/api/energy-usage/utility-upload"
    name = "api:energy_usage:utility_upload"
    requires_auth = True

    def __init__(self, hass):
        self.hass = hass
        self._lock = asyncio.Lock()
        self._store = Store(hass, 1, "energy_usage_pending_imports")
        self._pending = None

    async def _load_pending(self):
        if self._pending is None:
            saved = await self._store.async_load()
            self._pending = saved if isinstance(saved, dict) else {}

    async def _remember(self, entry, resource_ids):
        """Retain IDs, never XML or credentials, for interrupted imports."""
        await self._load_pending()
        previous = self._pending.get(entry.entry_id, [])
        if not isinstance(previous, list):
            previous = []
        ids = sorted(set(previous) | set(resource_ids))
        self._pending[entry.entry_id] = ids
        await self._store.async_save(self._pending)

    async def _forget(self, entry, resource_ids):
        await self._load_pending()
        old = self._pending.get(entry.entry_id, [])
        self._pending[entry.entry_id] = [
            item for item in old if item not in resource_ids
        ]
        await self._store.async_save(self._pending)

    async def _lookup(self, entry, resource_ids):
        api = self._api(entry)
        return [
            await api.resource_association(resource_id)
            for resource_id in resource_ids
        ]

    def _entry(self, request):
        user = request.get("hass_user")
        if user is None or not user.is_admin:
            raise web.HTTPForbidden(text="Administrator access required")
        entries = self.hass.config_entries.async_entries(DOMAIN)
        if len(entries) != 1:
            raise web.HTTPConflict(
                text="Exactly one Energy Usage entry is required"
            )
        return entries[0]

    def _api(self, entry):
        return EnergyApi(
            async_get_clientsession(self.hass),
            entry.data[CONF_URL], entry.data[CONF_TOKEN],
        )

    async def get(self, request):
        """List available acquisition sources for an HA administrator."""
        entry = self._entry(request)
        try:
            sources = await self._api(entry).acquisition_sources()
        except EnergyApiError as exc:
            raise web.HTTPBadGateway(
                text="Unable to retrieve acquisition sources"
            ) from exc
        try:
            meters = await self._api(entry).meters()
        except EnergyApiError as exc:
            raise web.HTTPBadGateway(
                text="Unable to retrieve physical meters"
            ) from exc
        allowed = {
            int(meter["id"])
            for meter in self.hass.data[DOMAIN][entry.entry_id]
            .data.get("meters", [])
            if int(meter.get("commodity", -1)) in (1, 7)
        }
        meters = [
            meter for meter in meters
            if type(meter.get("id")) is int
            and meter["id"] in allowed
        ]
        await self._load_pending()
        pending = self._pending.get(entry.entry_id, [])
        if any(
            type(item) is not int or item <= 0 for item in pending
        ):
            raise web.HTTPBadGateway(text="Invalid pending import state")
        # A backend outage must not erase the pending recovery journal.
        try:
            associations = await self._lookup(entry, pending[:128])
        except EnergyApiError as exc:
            raise web.HTTPBadGateway(
                text="Unable to verify pending resource associations"
            ) from exc
        return self.json({
            "sources": sources, "meters": meters,
            "pending_resources": associations,
            "pending_count": len(pending),
        })

    async def _sync(self, entry, meter_ids):
        """Reconcile only explicitly selected, registered meters."""
        coordinator = self.hass.data[DOMAIN][entry.entry_id]
        allowed = {
            int(meter["id"])
            for meter in coordinator.data.get("meters", [])
            if int(meter.get("commodity", -1)) in (1, 7)
        }
        if not meter_ids or not set(meter_ids) <= allowed:
            raise web.HTTPBadRequest(text="Invalid physical meter selection")
        for meter_id in sorted(set(meter_ids)):
            await sync_one(
                self.hass, entry, meter_id, runtime_for_entry(entry),
            )
        return sorted(set(meter_ids))

    async def _associate(self, entry, payload):
        """Associate every selected resource before scoped Recorder sync."""
        mappings = payload.get("associations")
        if not isinstance(mappings, list) or not mappings or len(mappings) > 128:
            raise web.HTTPBadRequest(text="Invalid resource associations")
        resource_ids = []
        meter_ids = []
        for item in mappings:
            if not isinstance(item, dict):
                raise web.HTTPBadRequest(text="Invalid resource association")
            resource_id = item.get("resource_id")
            meter_id = item.get("meter_id")
            if (type(resource_id) is not int or resource_id <= 0
                    or type(meter_id) is not int or meter_id <= 0):
                raise web.HTTPBadRequest(text="Invalid resource or meter ID")
            resource_ids.append(resource_id)
            meter_ids.append(meter_id)
        if len(set(resource_ids)) != len(resource_ids):
            raise web.HTTPBadRequest(text="Duplicate resource association")
        # Validate the entire batch before any backend mutation.
        allowed = {
            int(meter["id"])
            for meter in self.hass.data[DOMAIN][entry.entry_id]
            .data.get("meters", [])
            if int(meter.get("commodity", -1)) in (1, 7)
        }
        if not set(meter_ids) <= allowed:
            raise web.HTTPBadRequest(text="Unknown physical meter")
        api = self._api(entry)
        completed = []
        # Never submit a mapping that conflicts with canonical identity.
        try:
            states = await self._lookup(entry, resource_ids)
        except EnergyApiError as exc:
            raise web.HTTPBadGateway(
                text="Unable to verify resource associations"
            ) from exc
        conflicts = [
            state["resource_id"] for state, meter_id in zip(states, meter_ids)
            if state["physical_meter_id"] is not None
            and state["physical_meter_id"] != meter_id
        ]
        if conflicts:
            return self.json({
                "associated": [], "synchronized": False,
                "conflicting_resource_ids": conflicts,
                "error": "Existing association conflicts with selection",
            }, status_code=409)
        try:
            for state, meter_id in zip(states, meter_ids):
                if state["physical_meter_id"] == meter_id:
                    completed.append({
                        "resource_id": state["resource_id"],
                        "meter_id": meter_id,
                        "status": "already_associated",
                    })
                else:
                    completed.append(await api.associate_resource(
                        meter_id, state["resource_id"],
                    ))
        except EnergyApiError:
            _LOGGER.warning("Physical meter association incomplete")
            return self.json({
                "associated": completed, "synchronized": False,
                "error": "Meter association failed; review and retry",
            }, status_code=207)
        # Verify persisted association state before any Recorder operation.
        try:
            verified = await self._lookup(entry, resource_ids)
            if any(
                state["physical_meter_id"] != meter_id
                for state, meter_id in zip(verified, meter_ids)
            ):
                raise EnergyApiError("Association was not persisted")
        except EnergyApiError:
            return self.json({
                "associated": completed, "synchronized": False,
                "error": "Association verification failed; retry",
            }, status_code=207)
        try:
            synced = await self._sync(entry, meter_ids)
        except Exception:
            _LOGGER.exception("Scoped Recorder synchronization failed")
            return self.json({
                "associated": completed, "synchronized": False,
                "error": "Recorder synchronization failed; retry mappings",
            }, status_code=207)
        await self._forget(entry, resource_ids)
        return self.json({
            "associated": completed, "synchronized": True,
            "meter_ids": synced,
        })

    async def post(self, request):
        """Accept XML bytes and an existing acquisition source ID.

        Import never automatically synchronizes Recorder. Explicit
        resource associations are submitted in a separate request.
        """
        entry = self._entry(request)
        if self._lock.locked():
            raise web.HTTPConflict(text="Another import is in progress")
        async with self._lock:
            return await self._post_locked(request, entry)

    async def _post_locked(self, request, entry):
        """Serialize uploads and synchronization per integration."""
        payload = None
        if request.content_type == "application/json":
            # The dashboard card uses HA callApi, which sends JSON.
            if request.content_length and request.content_length > (
                11 * 1024 * 1024
            ):
                raise web.HTTPRequestEntityTooLarge(
                    max_size=11 * 1024 * 1024,
                    actual_size=request.content_length,
                )
            # Read the entire request with a bounded buffer before decoding.
            body = bytearray()
            async for chunk in request.content.iter_chunked(65536):
                body.extend(chunk)
                if len(body) > 11 * 1024 * 1024:
                    raise web.HTTPRequestEntityTooLarge(
                        max_size=11 * 1024 * 1024,
                        actual_size=len(body),
                    )
            try:
                payload = json.loads(body)
            except (ValueError, UnicodeDecodeError) as exc:
                raise web.HTTPBadRequest(text="Invalid JSON") from exc
            if not isinstance(payload, dict):
                raise web.HTTPBadRequest(text="Expected JSON object")
        if payload is not None and payload.get("sync_only") is True:
            raise web.HTTPBadRequest(
                text="Unscoped Recorder synchronization is disabled"
            )
        if payload is not None and "associations" in payload:
            return await self._associate(entry, payload)
        if (payload or request.query).get("sync") in ("1", 1, True):
            raise web.HTTPBadRequest(
                text="Associate imported resources before synchronization"
            )
        try:
            source_id = int(
                (payload or request.query).get("source_id", "")
            )
        except (ValueError, TypeError) as exc:
            raise web.HTTPBadRequest(text="Invalid source ID") from exc
        if source_id <= 0:
            raise web.HTTPBadRequest(text="Invalid source ID")
        if request.content_type not in (
            "application/xml", "text/xml", "application/json"
        ):
            raise web.HTTPUnsupportedMediaType(
                text="Expected XML content type"
            )
        if payload is None and request.content_length is not None:
            if request.content_length > MAX_XML_BYTES:
                raise web.HTTPRequestEntityTooLarge(
                    max_size=MAX_XML_BYTES,
                    actual_size=request.content_length,
                )
        if payload is not None:
            encoded = payload.get("xml_base64")
            if not isinstance(encoded, str) or len(encoded) > (
                (MAX_XML_BYTES + 2) // 3 * 4
            ):
                raise web.HTTPBadRequest(text="Invalid XML encoding")
            try:
                xml = base64.b64decode(encoded, validate=True)
            except (ValueError, binascii.Error) as exc:
                raise web.HTTPBadRequest(
                    text="Invalid base64 XML"
                ) from exc
        else:
            data = bytearray()
            async for chunk in request.content.iter_chunked(65536):
                data.extend(chunk)
                if len(data) > MAX_XML_BYTES:
                    raise web.HTTPRequestEntityTooLarge(
                        max_size=MAX_XML_BYTES, actual_size=len(data),
                    )
            xml = bytes(data)
        if not xml:
            raise web.HTTPBadRequest(text="Empty XML document")
        if len(xml) > MAX_XML_BYTES:
            raise web.HTTPRequestEntityTooLarge(
                max_size=MAX_XML_BYTES, actual_size=len(xml),
            )
        api = self._api(entry)
        # Validate the selected source against the backend source catalog.
        try:
            sources = await api.acquisition_sources()
        except EnergyApiError as exc:
            raise web.HTTPBadGateway(
                text="Unable to verify acquisition source"
            ) from exc
        if source_id not in {source["id"] for source in sources}:
            raise web.HTTPBadRequest(text="Unknown acquisition source")
        try:
            result = await api.import_green_button(source_id, xml)
        except EnergyAuthError as exc:
            raise web.HTTPBadGateway(
                text="Energy Ingest authentication failed"
            ) from exc
        except EnergyApiError as exc:
            raise web.HTTPBadGateway(
                text="Energy Ingest import failed"
            ) from exc

        # Canonical import succeeds independently of meter association.
        await self._remember(entry, result["resource_ids"])
        try:
            states = await self._lookup(entry, result["resource_ids"])
        except EnergyApiError:
            return self.json({
                "import": result, "associations": [],
                "synchronized": False,
                "error": "Import accepted; association lookup failed. "
                         "Use recovery to resume.",
            }, status_code=207)
        return self.json({
            "import": result, "associations": states,
            "synchronized": False,
        })
