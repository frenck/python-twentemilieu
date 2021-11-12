"""Asynchronous Python client for the Twente Milieu API."""
from __future__ import annotations

import asyncio
import json
import socket
from datetime import date, datetime, timedelta
from enum import IntEnum
from importlib import metadata
from typing import Any

import aiohttp
import async_timeout
from aiohttp.client import ClientSession
from attr import dataclass
from yarl import URL

from .exceptions import (
    TwenteMilieuAddressError,
    TwenteMilieuConnectionError,
    TwenteMilieuError,
)

API_COMPANY_CODE = "8d97bb56-5afd-4cbc-a651-b4f7314264b4"
API_HOST = "twentemilieuapi.ximmio.com"


class WasteType(IntEnum):
    """Enum for the types of waste."""

    NON_RECYCLABLE = 0
    ORGANIC = 1
    PAPER = 2
    PACKAGES = 10


@dataclass
class TwenteMilieu:
    """Main class for handling connections with Twente Milieu."""

    post_code: str
    house_number: str | int

    house_letter: str | int | None = None
    request_timeout: int = 10
    session: ClientSession | None = None

    _close_session: bool = False
    _unique_id: int | None = None

    async def _request(self, uri: str, *, data=None) -> dict[str, Any]:
        """Handle a request to the Twente Milieu API.

        A generic method for sending/handling HTTP requests done against
        the Twente Milieu API.

        Args:
            uri: Request URI
            data: Dictionary of data to send to the Twente Milieu API.

        Returns:
            A Python dictionary (JSON decoded) with the response from
            the Twente Milieu API.

        Raises:
            TwenteMilieuConnectionError: An error occurred while communicating with
                the Twente Milieu API.
            TwenteMilieuError: Received an unexpected response from the Twente
                Milieu API.
        """
        url = URL.build(scheme="https", host=API_HOST, port=443, path="/api/").join(
            URL(uri)
        )

        print(url)

        version = metadata.version(__package__)
        headers = {
            "User-Agent": f"PythonTwenteMilieu/{version}",
            "Accept": "application/json, text/plain, */*",
        }

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        try:
            async with async_timeout.timeout(self.request_timeout):
                response = await self.session.request(
                    "POST", url, json=data, headers=headers, ssl=True
                )
        except asyncio.TimeoutError as exception:
            raise TwenteMilieuConnectionError(
                "Timeout occurred while connecting to Twente Milieu API."
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            raise TwenteMilieuConnectionError(
                "Error occurred while communicating with Twente Milieu."
            ) from exception

        content_type = response.headers.get("Content-Type", "")
        if (response.status // 100) in [4, 5]:
            contents = await response.read()
            response.close()

            if content_type == "application/json":
                raise TwenteMilieuError(
                    response.status, json.loads(contents.decode("utf8"))
                )
            raise TwenteMilieuError(
                response.status, {"message": contents.decode("utf8")}
            )

        if "application/json" not in content_type:
            text = await response.text()
            raise TwenteMilieuError(
                "Unexpected response from the Twente Milieu API",
                {"Content-Type": content_type, "response": text},
            )

        return await response.json()

    async def unique_id(self) -> int:
        """Return unique address ID.

        Returns:
            Unique address ID.

        Raises:
            TwenteMilieuAddressError: Address could not be found.
        """
        if self._unique_id is None:
            response = await self._request(
                "FetchAdress",
                data={
                    "companyCode": API_COMPANY_CODE,
                    "postCode": self.post_code,
                    "houseNumber": str(self.house_number),
                    "houseLetter": str(self.house_letter)
                    if self.house_letter
                    else None,
                },
            )
            if "dataList" not in response or not response["dataList"]:
                raise TwenteMilieuAddressError(
                    "Address not found in Twente Milieu service area"
                )
            self._unique_id = response["dataList"][0]["UniqueId"]
        return self._unique_id

    async def update(self) -> dict[WasteType, date | None]:
        """Fetch data from Twente Milieu.

        Returns:
            A dictionary with the date for each waste type from Twente Milieu.
        """
        await self.unique_id()

        response = await self._request(
            "GetCalendar",
            data={
                "companyCode": API_COMPANY_CODE,
                "uniqueAddressID": self._unique_id,
                "startDate": (datetime.today() - timedelta(days=1)).date().isoformat(),
                "endDate": (datetime.today() + timedelta(days=100)).date().isoformat(),
            },
        )

        pickups: dict[WasteType, date | None] = {}
        for pickup in response["dataList"]:
            waste_type = WasteType(pickup["pickupType"])
            pickup_date = None
            if pickup["pickupDates"]:
                pickup_date = datetime.strptime(
                    min(pickup["pickupDates"]), "%Y-%m-%dT%H:%M:%S"
                ).date()
                if previous_pickup_date := pickups.get(waste_type):
                    pickup_date = min(pickup_date, previous_pickup_date)
            pickups[waste_type] = pickup_date

        return pickups

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self) -> TwenteMilieu:
        """Async enter.

        Returns:
            The TwenteMilieu object.
        """
        return self

    async def __aexit__(self, *_exc_info) -> None:
        """Async exit.

        Args:
            _exc_info: Exec type.
        """
        await self.close()
