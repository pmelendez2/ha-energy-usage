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
        return self.json({"sources": sources, "meters": meters})

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
        try:
            for resource_id, meter_id in zip(resource_ids, meter_ids):
                completed.append(await api.associate_resource(
                    meter_id, resource_id,
                ))
        except EnergyApiError:
            _LOGGER.warning("Physical meter association incomplete")
            return self.json({
                "associated": completed, "synchronized": False,
                "error": "Meter association failed; review and retry",
            }, status_code=207)
        try:
            synced = await self._sync(entry, meter_ids)
        except Exception:
            _LOGGER.exception("Scoped Recorder synchronization failed")
            return self.json({
                "associated": completed, "synchronized": False,
                "error": "Recorder synchronization failed; retry mappings",
            }, status_code=207)
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
        return self.json({"import": result, "synchronized": False})
