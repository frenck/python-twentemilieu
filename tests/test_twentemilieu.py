"""Tests for `twentemilieu.twentemilieu`."""

# pylint: disable=protected-access
import asyncio
import json
import socket
from datetime import date
from unittest.mock import patch

import aiohttp
import pytest
from aresponses import Response, ResponsesMockServer

from twentemilieu import TwenteMilieu, WasteType
from twentemilieu.exceptions import (
    TwenteMilieuAddressError,
    TwenteMilieuConnectionError,
    TwenteMilieuError,
)

API_HOST = "twentemilieuapi.ximmio.com"


async def test_json_request(aresponses: ResponsesMockServer) -> None:
    """Test JSON response is handled correctly."""
    aresponses.add(
        API_HOST,
        "/api/",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"status": "ok"}',
        ),
    )
    async with aiohttp.ClientSession() as session:
        twente = TwenteMilieu(post_code="1234AB", house_number=1, session=session)
        response = await twente._request("")
        assert response["status"] == "ok"
        await twente.close()


async def test_wastetype_fallback() -> None:
    """Test the WasteType fallback is handled correctly."""
    assert WasteType(56) == WasteType.PACKAGES, (
        "Fallback for high-density packages not handled!"
    )

    with pytest.raises(TypeError):
        WasteType._missing_("wrong_type")


async def test_internal_session(aresponses: ResponsesMockServer) -> None:
    """Test JSON response is handled correctly."""
    aresponses.add(
        API_HOST,
        "/api/",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"status": "ok"}',
        ),
    )
    async with TwenteMilieu(post_code="1234AB", house_number=1) as twente:
        response = await twente._request("")
        assert response["status"] == "ok"


async def test_internal_eventloop(aresponses: ResponsesMockServer) -> None:
    """Test JSON response is handled correctly."""
    aresponses.add(
        API_HOST,
        "/api/",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"status": "ok"}',
        ),
    )
    async with TwenteMilieu(post_code="1234AB", house_number=1) as twente:
        response = await twente._request("")
        assert response["status"] == "ok"


async def test_timeout(aresponses: ResponsesMockServer) -> None:
    """Test request timeout from Twente Milieu."""

    # Faking a timeout by sleeping
    async def response_handler(_: aiohttp.ClientResponse) -> Response:
        await asyncio.sleep(2)
        return aresponses.Response(body="Goodmorning!")

    aresponses.add(API_HOST, "/api/", "POST", response_handler)

    async with aiohttp.ClientSession() as session:
        twente = TwenteMilieu(
            post_code="1234AB",
            house_number=1,
            session=session,
            request_timeout=1,
        )
        with pytest.raises(TwenteMilieuConnectionError):
            assert await twente._request("")


async def test_http_error400(aresponses: ResponsesMockServer) -> None:
    """Test HTTP 404 response handling."""
    aresponses.add(
        API_HOST,
        "/api/",
        "POST",
        aresponses.Response(text="OMG PUPPIES!", status=404),
    )

    async with aiohttp.ClientSession() as session:
        twente = TwenteMilieu(post_code="1234AB", house_number=1, session=session)
        with pytest.raises(TwenteMilieuError):
            assert await twente._request("")


async def test_http_error500(aresponses: ResponsesMockServer) -> None:
    """Test HTTP 500 response handling."""
    aresponses.add(
        API_HOST,
        "/api/",
        "POST",
        aresponses.Response(
            body=b'{"status":"nok"}',
            status=500,
            headers={"Content-Type": "application/json"},
        ),
    )

    async with aiohttp.ClientSession() as session:
        twente = TwenteMilieu(post_code="1234AB", house_number=1, session=session)
        with pytest.raises(TwenteMilieuError):
            assert await twente._request("")


async def test_unexpected_response(aresponses: ResponsesMockServer) -> None:
    """Test unexpected response handling."""
    aresponses.add(
        API_HOST,
        "/api/",
        "POST",
        aresponses.Response(text="OMG PUPPIES!", status=200),
    )

    async with aiohttp.ClientSession() as session:
        twente = TwenteMilieu(post_code="1234AB", house_number=1, session=session)
        with pytest.raises(TwenteMilieuError):
            assert await twente._request("")


async def test_communication_error() -> None:
    """Test communication error handling."""
    async with aiohttp.ClientSession() as session:
        twente = TwenteMilieu(post_code="1234AB", house_number=1, session=session)
        with (
            patch.object(
                session,
                "request",
                side_effect=socket.gaierror,
            ),
            pytest.raises(TwenteMilieuConnectionError),
        ):
            assert await twente._request("")


async def test_unique_id(aresponses: ResponsesMockServer) -> None:
    """Test request of a unique address identifier."""
    aresponses.add(
        API_HOST,
        "/api/FetchAdress",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"dataList": [{"UniqueId": "12345"}]}',
        ),
    )
    async with aiohttp.ClientSession() as session:
        twente = TwenteMilieu(post_code="1234AB", house_number=1, session=session)
        unique_id = await twente.unique_id()
        assert unique_id == "12345"
        unique_id = await twente.unique_id()
        assert unique_id == "12345"


async def test_invalid_address(aresponses: ResponsesMockServer) -> None:
    """Test request of invalid address information."""
    aresponses.add(
        API_HOST,
        "/api/FetchAdress",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"dataList": []}',
        ),
    )
    async with aiohttp.ClientSession() as session:
        twente = TwenteMilieu(post_code="1234AB", house_number=1, session=session)
        with pytest.raises(TwenteMilieuAddressError):
            assert await twente.unique_id()


async def test_update(aresponses: ResponsesMockServer) -> None:
    """Test request for updating data from Twente Milieu."""
    aresponses.add(
        API_HOST,
        "/api/FetchAdress",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"dataList": [{"UniqueId": "12345"}]}',
        ),
    )
    aresponses.add(
        API_HOST,
        "/api/GetCalendar",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=json.dumps(
                {
                    "dataList": [
                        {
                            "pickupDates": [
                                "2019-07-20T00:00:00",
                                "2019-07-19T00:00:00",
                            ],
                            "pickupType": 1,
                        },
                        {
                            "pickupDates": ["2019-07-21T00:00:00"],
                            "pickupType": 0,
                        },
                        {
                            "pickupDates": ["2019-08-22T00:00:00"],
                            "pickupType": 0,
                        },
                        {
                            "pickupDates": ["2019-07-22T00:00:00"],
                            "pickupType": 2,
                        },
                        {
                            "pickupDates": ["2019-07-23T00:00:00"],
                            "pickupType": 56,
                        },
                        {"pickupDates": [], "pickupType": 10},
                    ],
                },
            ),
        ),
    )

    async with aiohttp.ClientSession() as session:
        twente = TwenteMilieu(post_code="1234AB", house_number=1, session=session)
        pickups = await twente.update()

        assert pickups[WasteType.NON_RECYCLABLE] == [
            date(2019, 7, 21),
            date(2019, 8, 22),
        ]
        assert pickups[WasteType.ORGANIC] == [date(2019, 7, 19), date(2019, 7, 20)]
        assert pickups[WasteType.PAPER] == [date(2019, 7, 22)]
        assert pickups[WasteType.PACKAGES] == [date(2019, 7, 23)]
