# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Project Contributors
"""Client for the authenticated, read-only Energy Ingest API."""

from urllib.parse import urlencode, urlsplit
from datetime import datetime, timedelta

from aiohttp import ClientError, ClientSession, ClientTimeout


class EnergyApiError(Exception):
    """The API was unavailable or supplied an invalid response."""


class EnergyAuthError(EnergyApiError):
    """The API token was rejected."""


class EnergyApi:
    """A small, bounded-time API client; never log credentials."""

    def __init__(self, session: ClientSession, url: str, token: str):
        url = url.rstrip("/")
        parsed = urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError("Invalid Energy Ingest URL")
        if (parsed.username or parsed.password or parsed.query
                or parsed.fragment or parsed.path):
            raise ValueError("URL must not contain credentials or queries")
        self._session = session
        self._url = url
        self._token = token

    async def _get(self, path: str):
        try:
            async with self._session.get(
                self._url + path,
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=ClientTimeout(total=30),
            ) as response:
                if response.status in (401, 403):
                    raise EnergyAuthError("Authentication failed")
                if response.status != 200:
                    raise EnergyApiError(
                        f"Energy Ingest API returned HTTP {response.status}"
                    )
                return await response.json(content_type=None)
        except EnergyApiError:
            raise
        except (ClientError, TimeoutError, ValueError) as exc:
            raise EnergyApiError(
                "Cannot communicate with Energy Ingest"
            ) from exc

    async def acquisition_sources(self):
        """Return configured source IDs and display names."""
        data = await self._get("/v1/acquisition-sources")
        if not isinstance(data, list) or any(
            not isinstance(item, dict)
            or type(item.get("id")) is not int
            or item["id"] <= 0
            or not isinstance(item.get("name"), str)
            for item in data
        ):
            raise EnergyApiError("Invalid acquisition sources")
        return data

    async def meters(self):
        data = await self._get("/v1/meters")
        if not isinstance(data, list):
            raise EnergyApiError("Unexpected meter response")
        return data

    async def resource_association(self, resource_id: int):
        """Read Energy Ingest's canonical resource-to-meter association."""
        if type(resource_id) is not int or resource_id <= 0:
            raise ValueError("Invalid reading resource ID")
        data = await self._get(
            f"/v1/resources/{resource_id}/association"
        )
        if not isinstance(data, dict) or data.get("resource_id") != resource_id:
            raise EnergyApiError("Invalid resource association response")
        meter_id = data.get("physical_meter_id")
        status = data.get("status")
        if status == "unassociated" and meter_id is None:
            return data
        if (status == "associated" and type(meter_id) is int
                and meter_id > 0):
            return data
        raise EnergyApiError("Invalid resource association state")

    async def window(
        self, meter_id: int, start: datetime, end: datetime
    ) -> dict:
        """Retrieve readings for a UTC date range (end excluded)."""
        if type(meter_id) is not int or meter_id <= 0:
            raise ValueError("Invalid physical meter ID")
        if not isinstance(start, datetime) or not isinstance(end, datetime):
            raise ValueError("Usage date range requires start and end timestamps")
        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError("Usage date range timestamps must include a timezone")
        if start.utcoffset() != timedelta(0) or end.utcoffset() != timedelta(0):
            raise ValueError("Usage date range timestamps must be in UTC internally")
        if start.microsecond or end.microsecond:
            raise ValueError("Usage date range timestamps must use whole seconds")
        if not start < end <= start + timedelta(days=31):
            raise ValueError("Usage date range must be longer than zero and at most 31 days")
        start_str = start.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = end.strftime("%Y-%m-%dT%H:%M:%SZ")
        query = urlencode({"start": start_str, "end": end_str})
        data = await self._get(f"/v1/meters/{meter_id}/window?{query}")
        if not isinstance(data, dict):
            raise EnergyApiError("Unexpected usage date range response")
        if data.get("physical_meter_id") != meter_id:
            raise EnergyApiError("Usage date range response belongs to another meter")
        if data.get("resolved") is not True or data.get("issues"):
            raise EnergyApiError("Some usage readings could not be verified")
        if not isinstance(data.get("intervals"), list):
            raise EnergyApiError("Usage date range response is missing readings")
        return data

    async def stream(self, meter_id: int):
        data = await self._get(f"/v1/meters/{int(meter_id)}/stream")
        if not isinstance(data, dict):
            raise EnergyApiError("Unexpected stream response")
        return data

    async def associate_resource(self, meter_id: int, resource_id: int):
        """Attach an imported reading resource to a selected physical meter."""
        if type(meter_id) is not int or meter_id <= 0:
            raise ValueError("Invalid physical meter ID")
        if type(resource_id) is not int or resource_id <= 0:
            raise ValueError("Invalid reading resource ID")
        try:
            async with self._session.post(
                self._url + f"/v1/meters/{meter_id}/resources",
                json={"resource_id": resource_id},
                headers={
                    "Authorization": f"Bearer {self._token}",
                },
                timeout=ClientTimeout(total=30),
            ) as response:
                if response.status in (401, 403):
                    raise EnergyAuthError("Authentication failed")
                if response.status == 409:
                    raise EnergyApiError(
                        "Reading resource does not match this meter "
                        "or is already assigned elsewhere"
                    )
                if response.status != 200:
                    raise EnergyApiError(
                        "Meter association returned HTTP "
                        f"{response.status}"
                    )
                result = await response.json(content_type=None)
        except EnergyApiError:
            raise
        except (ClientError, TimeoutError, ValueError) as exc:
            raise EnergyApiError("Meter association failed") from exc
        if (
            not isinstance(result, dict)
            or result.get("meter_id") != meter_id
            or result.get("resource_id") != resource_id
            or result.get("status") not in (
                "associated", "already_associated"
            )
        ):
            raise EnergyApiError("Invalid meter association response")
        return result

    async def import_green_button(self, source_id: int, xml: bytes):
        """Import one XML document using the authenticated backend API.

        The source ID is an acquisition source, not a meter identifier.
        The backend alone decides which observations are accepted.
        """
        if type(source_id) is not int or source_id <= 0:
            raise ValueError("Invalid acquisition source ID")
        if not isinstance(xml, bytes) or not xml:
            raise ValueError("Expected nonempty XML bytes")
        if len(xml) > 8 * 1024 * 1024:
            raise ValueError("XML exceeds the 8 MiB upload limit")
        try:
            async with self._session.post(
                self._url + "/v1/imports/green-button?" +
                urlencode({"source_id": source_id}),
                data=xml,
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/xml",
                },
                timeout=ClientTimeout(total=120),
            ) as response:
                if response.status in (401, 403):
                    raise EnergyAuthError("Authentication failed")
                if response.status != 200:
                    raise EnergyApiError(
                        f"Energy Ingest import returned HTTP {response.status}"
                    )
                result = await response.json(content_type=None)
        except EnergyApiError:
            raise
        except (ClientError, TimeoutError, ValueError) as exc:
            raise EnergyApiError("Energy Ingest import failed") from exc
        if not isinstance(result, dict) or any(
            type(result.get(key)) is not int or result[key] < 0
            for key in ("observations", "unchanged", "accepted")
        ):
            raise EnergyApiError("Invalid Energy Ingest import result")
        resource_ids = result.get("resource_ids")
        if (
            not isinstance(resource_ids, list)
            or any(
                type(resource_id) is not int or resource_id <= 0
                for resource_id in resource_ids
            )
            or len(set(resource_ids)) != len(resource_ids)
        ):
            raise EnergyApiError("Invalid imported reading resource IDs")
        return result
