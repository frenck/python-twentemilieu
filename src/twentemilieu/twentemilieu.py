"""Asynchronous Python client for the Twente Milieu API."""

from __future__ import annotations

import asyncio
import json
import socket
from datetime import date, datetime, timedelta
from enum import IntEnum
from importlib import metadata
from typing import Any, Self
from zoneinfo import ZoneInfo

import aiohttp
from aiohttp.client import ClientSession
from attr import dataclass
from yarl import URL

from .exceptions import (
    TwenteMilieuAddressError,
    TwenteMilieuConnectionError,
    TwenteMilieuError,
)

TIMEZONE_INFO = ZoneInfo("Europe/Amsterdam")


class WasteType(IntEnum):
    """Enum for the types of waste."""

    NON_RECYCLABLE = 0
    ORGANIC = 1
    PAPER = 2
    TREE = 6
    PACKAGES = 10

    @classmethod
    def _missing_(cls, value: object) -> WasteType:
        """Fallback for unknown waste types.

        Some waste types returned from the Twente Milieu API are semantically the same
        as some types already defined in this enum. This maps the API value to the
        correct enum value.

        An example would be for packages. Some housing has a container for packages,
        and high-density living may need to place their packages at a central point
        for pick-up. Both is a pick-up for packages, but their waste type returned
        from the API are different.

        """
        if not isinstance(value, int):
            raise TypeError(value)

        return {
            56: WasteType.PACKAGES,
        }[value]


@dataclass
class TwenteMilieu:
    """Main class for handling connections with Twente Milieu."""

    post_code: str
    house_number: str | int

    company_code: str = "8d97bb56-5afd-4cbc-a651-b4f7314264b4"
    api_host: str = "twentemilieuapi.ximmio.com"
    house_letter: str | int = ""
    request_timeout: int = 10
    session: ClientSession | None = None

    _close_session: bool = False
    _unique_id: int | None = None

    async def _request(self, uri: str, *, data: dict[str, Any] | None = None) -> Any:
        """Handle a request to the Twente Milieu API.

        A generic method for sending/handling HTTP requests done against
        the Twente Milieu API.

        Args:
        ----
            uri: Request URI
            data: Dictionary of data to send to the Twente Milieu API.

        Returns:
        -------
            A Python dictionary (JSON decoded) with the response from
            the Twente Milieu API.

        Raises:
        ------
            TwenteMilieuConnectionError: An error occurred while communicating with
                the Twente Milieu API.
            TwenteMilieuError: Received an unexpected response from the Twente
                Milieu API.

        """
        url = URL.build(
            scheme="https",
            host=self.api_host,
            port=443,
            path="/api/",
        ).join(URL(uri))

        version = metadata.version(__package__)
        headers = {
            "User-Agent": f"PythonTwenteMilieu/{version}",
            "Accept": "application/json, text/plain, */*",
        }

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        try:
            async with asyncio.timeout(self.request_timeout):
                response = await self.session.request(
                    "POST",
                    url,
                    json=data,
                    headers=headers,
                    ssl=True,
                )
        except asyncio.TimeoutError as exception:
            msg = "Timeout occurred while connecting to Twente Milieu API."
            raise TwenteMilieuConnectionError(msg) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = "Error occurred while communicating with Twente Milieu API."
            raise TwenteMilieuConnectionError(msg) from exception

        content_type = response.headers.get("Content-Type", "")
        if (response.status // 100) in [4, 5]:
            contents = await response.read()
            response.close()

            if content_type == "application/json":
                raise TwenteMilieuError(
                    response.status,
                    json.loads(contents.decode("utf8")),
                )
            raise TwenteMilieuError(
                response.status,
                {"message": contents.decode("utf8")},
            )

        if "application/json" not in content_type:
            text = await response.text()
            msg = "Unexpected response from the Twente Milieu API"
            raise TwenteMilieuError(
                msg,
                {"Content-Type": content_type, "response": text},
            )

        return await response.json()

    async def unique_id(self) -> int:
        """Return unique address ID.

        Returns
        -------
            Unique address ID.

        Raises
        ------
            TwenteMilieuAddressError: Address could not be found.

        """
        if self._unique_id is None:
            response = await self._request(
                "FetchAdress",
                data={
                    "companyCode": self.company_code,
                    "postCode": self.post_code.replace(" ", "").upper(),
                    "houseNumber": str(self.house_number),
                    "houseLetter": str(self.house_letter or ""),
                },
            )
            if "dataList" not in response or not response["dataList"]:
                msg = "Address not found in Twente Milieu service area"
                raise TwenteMilieuAddressError(msg)
            self._unique_id = response["dataList"][0]["UniqueId"]
        return self._unique_id

    async def update(self) -> dict[WasteType, list[date]]:
        """Fetch data from Twente Milieu.

        Returns
        -------
            A dictionary with the date for each waste type from Twente Milieu.

        """
        await self.unique_id()

        response = await self._request(
            "GetCalendar",
            data={
                "companyCode": self.company_code,
                "uniqueAddressID": self._unique_id,
                "startDate": (datetime.now(tz=TIMEZONE_INFO) - timedelta(days=1))
                .date()
                .isoformat(),
                "endDate": (datetime.now(tz=TIMEZONE_INFO) + timedelta(days=365))
                .date()
                .isoformat(),
            },
        )

        pickups: dict[WasteType, list[date]] = {
            waste_type: [] for waste_type in WasteType
        }
        for pickup in response["dataList"]:
            if not pickup["pickupDates"]:
                continue
            waste_type = WasteType(pickup["pickupType"])
            for pickup_date_raw in pickup["pickupDates"]:
                pickup_date = (
                    datetime.strptime(
                        pickup_date_raw,
                        "%Y-%m-%dT%H:%M:%S",
                    )
                    .replace(tzinfo=TIMEZONE_INFO)
                    .date()
                )
                pickups[waste_type].append(pickup_date)

        # Sort all pickups by date
        for waste_type in pickups:  # noqa: PLC0206
            pickups[waste_type].sort()

        return pickups

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self) -> Self:
        """Async enter.

        Returns
        -------
            The TwenteMilieu object.

        """
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit.

        Args:
        ----
            _exc_info: Exec type.

        """
        await self.close()
