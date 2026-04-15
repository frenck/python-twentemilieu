"""Tests for `twentemilieu.twentemilieu`."""

from __future__ import annotations

# pylint: disable=protected-access,redefined-outer-name
import socket
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import aiohttp
import pytest
from aioresponses import aioresponses

from twentemilieu import TwenteMilieu, WasteType
from twentemilieu.exceptions import (
    TwenteMilieuAddressError,
    TwenteMilieuConnectionError,
    TwenteMilieuError,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

    from syrupy.assertion import SnapshotAssertion

API_BASE = "https://twentemilieuapi.ximmio.com/api/"
API_URL = API_BASE
API_FETCH_ADDRESS = API_BASE + "FetchAdress"
API_GET_CALENDAR = API_BASE + "GetCalendar"


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


async def test_json_request(twente: TwenteMilieu) -> None:
    """Test JSON response is handled correctly."""
    with aioresponses() as mocked:
        mocked.post(
            API_URL,
            status=200,
            payload={"status": "ok"},
        )
        response = await twente._request("")
        assert response["status"] == "ok"


async def test_wastetype_fallback() -> None:
    """Test the WasteType fallback is handled correctly."""
    # Known alias for high-density packages pickup points.
    assert WasteType(56) == WasteType.PACKAGES, (
        "Fallback for high-density packages not handled!"
    )

    # Unknown integer values must raise ValueError rather than KeyError
    # so callers can catch and skip forward-compatibly.
    with pytest.raises(ValueError, match="is not a valid WasteType"):
        WasteType(999)

    # Non-integer values still raise TypeError from the _missing_ hook.
    with pytest.raises(TypeError):
        WasteType._missing_("wrong_type")


async def test_internal_session() -> None:
    """Test the TwenteMilieu client manages its own session as a context manager."""
    with aioresponses() as mocked:
        mocked.post(
            API_URL,
            status=200,
            payload={"status": "ok"},
        )
        async with TwenteMilieu(post_code="1234AB", house_number=1) as client:
            response = await client._request("")
            assert response["status"] == "ok"


async def test_timeout(twente: TwenteMilieu) -> None:
    """Test request timeout from Twente Milieu."""
    twente.request_timeout = 1
    with aioresponses() as mocked:
        mocked.post(API_URL, exception=TimeoutError())
        with pytest.raises(TwenteMilieuConnectionError):
            await twente._request("")


def _mock_http_4xx_plaintext(mocked: aioresponses) -> None:
    mocked.post(API_URL, status=404, body="OMG PUPPIES!", content_type="text/plain")


def _mock_http_5xx_json(mocked: aioresponses) -> None:
    mocked.post(
        API_URL,
        status=500,
        body=b'{"status":"nok"}',
        content_type="application/json",
    )


def _mock_200_unexpected_content_type(mocked: aioresponses) -> None:
    mocked.post(API_URL, status=200, body="OMG PUPPIES!", content_type="text/plain")


@pytest.mark.parametrize(
    "setup_mock",
    [
        pytest.param(_mock_http_4xx_plaintext, id="http_4xx_plaintext"),
        pytest.param(_mock_http_5xx_json, id="http_5xx_json"),
        pytest.param(
            _mock_200_unexpected_content_type,
            id="200_unexpected_content_type",
        ),
    ],
)
async def test_request_errors(
    twente: TwenteMilieu,
    setup_mock: Callable[[aioresponses], None],
) -> None:
    """Test bad API responses raise TwenteMilieuError."""
    with aioresponses() as mocked:
        setup_mock(mocked)
        with pytest.raises(TwenteMilieuError):
            await twente._request("")


async def test_communication_error(twente: TwenteMilieu) -> None:
    """Test communication error handling."""
    with (
        patch.object(twente.session, "request", side_effect=socket.gaierror),
        pytest.raises(TwenteMilieuConnectionError),
    ):
        await twente._request("")


async def test_unique_id(twente: TwenteMilieu) -> None:
    """Test request of a unique address identifier."""
    with aioresponses() as mocked:
        mocked.post(
            API_FETCH_ADDRESS,
            status=200,
            payload={"dataList": [{"UniqueId": "12345"}]},
        )
        unique_id = await twente.unique_id()
        assert unique_id == "12345"
        unique_id = await twente.unique_id()
        assert unique_id == "12345"


async def test_invalid_address(twente: TwenteMilieu) -> None:
    """Test request of invalid address information."""
    with aioresponses() as mocked:
        mocked.post(
            API_FETCH_ADDRESS,
            status=200,
            payload={"dataList": []},
        )
        with pytest.raises(TwenteMilieuAddressError):
            await twente.unique_id()


async def test_update(
    twente: TwenteMilieu,
    calendar_response: Any,
    snapshot: SnapshotAssertion,
) -> None:
    """Test request for updating data from Twente Milieu."""
    with aioresponses() as mocked:
        mocked.post(
            API_FETCH_ADDRESS,
            status=200,
            payload={"dataList": [{"UniqueId": "12345"}]},
        )
        mocked.post(
            API_GET_CALENDAR,
            status=200,
            payload=calendar_response,
        )
        pickups = await twente.update()
        assert pickups == snapshot
