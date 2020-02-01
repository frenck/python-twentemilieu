# -*- coding: utf-8 -*-
"""Asynchronous Python client for the WasteAPI."""
import asyncio
import json
import socket
from datetime import datetime, timedelta
from typing import Dict, Optional

import aiohttp
import async_timeout
from yarl import URL

from .__version__ import __version__
from .const import API_BASE_URI, API_HOST, API_TO_WASTE_TYPE
from .exceptions import WasteApiAddressError, WasteApiConnectionError, WasteApiError


class WasteApi:
    """Main class for handling connections with WasteAPI."""

    def __init__(
        self,
        company_code: str,
        post_code: str,
        house_number: str,
        house_letter: str = None,
        loop=None,
        request_timeout: int = 10,
        session=None,
        user_agent: str = None,
    ):
        """Initialize connection with WasteAPI."""
        self._loop = loop
        self._session = session
        self._close_session = False

        self.company_code = company_code
        self.post_code = post_code
        self.house_number = house_number
        self.house_letter = house_letter

        self.request_timeout = request_timeout
        self.user_agent = user_agent

        self._unique_id = None
        self._pickup = {}  # type: Dict[str, datetime]

        if self._loop is None:
            self._loop = asyncio.get_event_loop()

        if self._session is None:
            self._session = aiohttp.ClientSession(loop=self._loop)
            self._close_session = True

        if self.user_agent is None:
            self.user_agent = "PythonWasteAPI/{}".format(__version__)

    async def _request(self, uri: str, method: str = "POST", data=None):
        """Handle a request to WasteAPI."""
        url = URL.build(
            scheme="https", host=API_HOST, port=443, path=API_BASE_URI
        ).join(URL(uri))

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json, text/plain, */*",
        }

        try:
            with async_timeout.timeout(self.request_timeout):
                response = await self._session.request(
                    method, url, data=data, headers=headers, ssl=True
                )
        except asyncio.TimeoutError as exception:
            raise WasteApiConnectionError(
                "Timeout occurred while connecting to WasteAPI."
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            raise WasteApiConnectionError(
                "Error occurred while communicating with WasteAPI."
            ) from exception

        content_type = response.headers.get("Content-Type", "")
        if (response.status // 100) in [4, 5]:
            contents = await response.read()
            response.close()

            if content_type == "application/json":
                raise WasteApiError(
                    response.status, json.loads(contents.decode("utf8"))
                )
            raise WasteApiError(response.status, {"message": contents.decode("utf8")})

        if "application/json" in response.headers["Content-Type"]:
            return await response.json()
        return await response.text()

    async def unique_id(self) -> Optional[int]:
        """Return unique address ID."""
        if self._unique_id is None:
            response = await self._request(
                "FetchAdress",
                data={
                    "companyCode": self.company_code,
                    "postCode": self.post_code,
                    "houseNumber": self.house_number,
                    "houseLetter": self.house_letter or "",
                },
            )
            if not response.get("dataList"):
                raise WasteApiAddressError("Address not found in WasteAPI service area")
            self._unique_id = response["dataList"][0]["UniqueId"]
        return self._unique_id

    async def update(self) -> None:
        """Fetch data from WasteAPI."""
        await self.unique_id()

        today = datetime.now().date()
        response = await self._request(
            "GetCalendar",
            data={
                "companyCode": self.company_code,
                "uniqueAddressID": self._unique_id,
                "startDate": today.isoformat(),
                "endDate": (today + timedelta(days=100)).isoformat(),
            },
        )

        for pickup in response["dataList"]:
            waste_type = API_TO_WASTE_TYPE.get(pickup["_pickupTypeText"])
            pickup_date = None
            if pickup["pickupDates"]:
                pickup_date = datetime.strptime(
                    min(pickup["pickupDates"]), "%Y-%m-%dT%H:%M:%S"
                )
            self._pickup.update({waste_type: pickup_date})  # type: ignore

    async def next_pickup(self, waste_type: str) -> Optional[datetime]:
        """Return date of next pickup of the requested waste type."""
        return self._pickup.get(waste_type)

    async def close(self) -> None:
        """Close open client session."""
        if self._close_session:
            await self._session.close()

    async def __aenter__(self) -> "WasteApi":
        """Async enter."""
        return self

    async def __aexit__(self, *exc_info) -> None:
        """Async exit."""
        await self.close()
