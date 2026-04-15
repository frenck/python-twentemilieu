"""Tests for `twentemilieu.twentemilieu`."""

from __future__ import annotations

# pylint: disable=protected-access,redefined-outer-name
import asyncio
import json
import socket
from typing import TYPE_CHECKING, Any
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

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from syrupy.assertion import SnapshotAssertion

API_HOST = "twentemilieuapi.ximmio.com"


@pytest.fixture
async def twente() -> AsyncIterator[TwenteMilieu]:
    """Return a TwenteMilieu client wired to a live aiohttp session."""
    async with aiohttp.ClientSession() as session:
        client = TwenteMilieu(
            post_code="1234AB",
            house_number=1,
            session=session,
        )
        yield client
        await client.close()


async def test_json_request(
    aresponses: ResponsesMockServer,
    twente: TwenteMilieu,
) -> None:
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
    response = await twente._request("")
    assert response["status"] == "ok"


async def test_wastetype_fallback() -> None:
    """Test the WasteType fallback is handled correctly."""
    assert WasteType(56) == WasteType.PACKAGES, (
        "Fallback for high-density packages not handled!"
    )

    with pytest.raises(TypeError):
        WasteType._missing_("wrong_type")


async def test_internal_session(aresponses: ResponsesMockServer) -> None:
    """Test the TwenteMilieu client manages its own session as a context manager."""
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
    async with TwenteMilieu(post_code="1234AB", house_number=1) as client:
        response = await client._request("")
        assert response["status"] == "ok"


async def test_timeout(aresponses: ResponsesMockServer) -> None:
    """Test request timeout from Twente Milieu."""

    # Faking a timeout by sleeping
    async def response_handler(_: aiohttp.ClientResponse) -> Response:
        await asyncio.sleep(2)
        return aresponses.Response(body="Good morning!")

    aresponses.add(API_HOST, "/api/", "POST", response_handler)

    async with aiohttp.ClientSession() as session:
        client = TwenteMilieu(
            post_code="1234AB",
            house_number=1,
            session=session,
            request_timeout=1,
        )
        with pytest.raises(TwenteMilieuConnectionError):
            assert await client._request("")


@pytest.mark.parametrize(
    "response_kwargs",
    [
        pytest.param(
            {"text": "OMG PUPPIES!", "status": 404},
            id="http_4xx_plaintext",
        ),
        pytest.param(
            {
                "body": b'{"status":"nok"}',
                "status": 500,
                "headers": {"Content-Type": "application/json"},
            },
            id="http_5xx_json",
        ),
        pytest.param(
            {"text": "OMG PUPPIES!", "status": 200},
            id="200_unexpected_content_type",
        ),
    ],
)
async def test_request_errors(
    aresponses: ResponsesMockServer,
    twente: TwenteMilieu,
    response_kwargs: dict[str, Any],
) -> None:
    """Test bad API responses raise TwenteMilieuError."""
    aresponses.add(
        API_HOST,
        "/api/",
        "POST",
        aresponses.Response(**response_kwargs),
    )
    with pytest.raises(TwenteMilieuError):
        await twente._request("")


async def test_communication_error(twente: TwenteMilieu) -> None:
    """Test communication error handling."""
    with (
        patch.object(twente.session, "request", side_effect=socket.gaierror),
        pytest.raises(TwenteMilieuConnectionError),
    ):
        await twente._request("")


async def test_unique_id(
    aresponses: ResponsesMockServer,
    twente: TwenteMilieu,
) -> None:
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
    unique_id = await twente.unique_id()
    assert unique_id == "12345"
    unique_id = await twente.unique_id()
    assert unique_id == "12345"


async def test_invalid_address(
    aresponses: ResponsesMockServer,
    twente: TwenteMilieu,
) -> None:
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
    with pytest.raises(TwenteMilieuAddressError):
        await twente.unique_id()


async def test_update(
    aresponses: ResponsesMockServer,
    twente: TwenteMilieu,
    calendar_response: Any,
    snapshot: SnapshotAssertion,
) -> None:
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
            text=json.dumps(calendar_response),
        ),
    )

    pickups = await twente.update()
    assert pickups == snapshot
