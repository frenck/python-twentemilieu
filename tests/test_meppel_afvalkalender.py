# -*- coding: utf-8 -*-
"""Tests for `meppel_afvalkalender.meppel_afvalkalender`."""
import asyncio
import json
from datetime import datetime

import aiohttp
import pytest
from meppel_afvalkalender import MeppelAfvalkalender
from meppel_afvalkalender.__version__ import __version__
from meppel_afvalkalender.const import (
    API_BASE_URI,
    API_HOST,
    WASTE_TYPE_NON_RECYCLABLE,
    WASTE_TYPE_ORGANIC,
    WASTE_TYPE_PAPER,
    WASTE_TYPE_PLASTIC,
)
from meppel_afvalkalender.exceptions import (
    MeppelAfvalkalenderAddressError,
    MeppelAfvalkalenderConnectionError,
    MeppelAfvalkalenderError,
)


@pytest.mark.asyncio
async def test_json_request(event_loop, aresponses):
    """Test JSON response is handled correctly."""
    aresponses.add(
        API_HOST,
        API_BASE_URI,
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"status": "ok"}',
        ),
    )
    async with aiohttp.ClientSession(loop=event_loop) as session:
        tw = MeppelAfvalkalender(
            post_code="1234AB", house_number=1, session=session, loop=event_loop
        )
        response = await tw._request("")
        assert response["status"] == "ok"


@pytest.mark.asyncio
async def test_text_request(event_loop, aresponses):
    """Test non JSON response is handled correctly."""
    aresponses.add(
        API_HOST, API_BASE_URI, "POST", aresponses.Response(status=200, text="OK")
    )
    async with aiohttp.ClientSession(loop=event_loop) as session:
        tw = MeppelAfvalkalender(
            post_code="1234AB", house_number=1, session=session, loop=event_loop
        )
        response = await tw._request("")
        assert response == "OK"


@pytest.mark.asyncio
async def test_internal_session(event_loop, aresponses):
    """Test JSON response is handled correctly."""
    aresponses.add(
        API_HOST,
        API_BASE_URI,
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"status": "ok"}',
        ),
    )
    async with MeppelAfvalkalender(
        post_code="1234AB", house_number=1, loop=event_loop
    ) as tw:
        response = await tw._request("")
        assert response["status"] == "ok"


@pytest.mark.asyncio
async def test_internal_eventloop(aresponses):
    """Test JSON response is handled correctly."""
    aresponses.add(
        API_HOST,
        API_BASE_URI,
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"status": "ok"}',
        ),
    )
    async with MeppelAfvalkalender(post_code="1234AB", house_number=1) as tw:
        response = await tw._request("")
        assert response["status"] == "ok"


@pytest.mark.asyncio
async def test_request_user_agent(event_loop, aresponses):
    """Test if client is sending correct user agent headers."""
    # Handle to run asserts on request in
    async def response_handler(request):
        assert request.headers["User-Agent"] == "PythonMeppelAfvalkalender/{}".format(
            __version__
        )
        return aresponses.Response(text="TEDDYBEAR", status=200)

    aresponses.add(API_HOST, API_BASE_URI, "POST", response_handler)

    async with aiohttp.ClientSession(loop=event_loop) as session:
        tw = MeppelAfvalkalender(
            post_code="1234AB", house_number=1, session=session, loop=event_loop
        )
        await tw._request("")


@pytest.mark.asyncio
async def test_request_custom_user_agent(event_loop, aresponses):
    """Test if client is sending correct user agent headers."""
    # Handle to run asserts on request in
    async def response_handler(request):
        assert request.headers["User-Agent"] == "LoremIpsum/1.0"
        return aresponses.Response(text="TEDDYBEAR", status=200)

    aresponses.add(API_HOST, API_BASE_URI, "POST", response_handler)

    async with aiohttp.ClientSession(loop=event_loop) as session:
        tw = MeppelAfvalkalender(
            post_code="1234AB",
            house_number=1,
            session=session,
            loop=event_loop,
            user_agent="LoremIpsum/1.0",
        )
        await tw._request("")


@pytest.mark.asyncio
async def test_timeout(event_loop, aresponses):
    """Test request timeout from Meppel Afvalkalender."""
    # Faking a timeout by sleeping
    async def response_handler(_):
        await asyncio.sleep(2)
        return aresponses.Response(body="Goodmorning!")

    aresponses.add(API_HOST, API_BASE_URI, "POST", response_handler)

    async with aiohttp.ClientSession(loop=event_loop) as session:
        tw = MeppelAfvalkalender(
            post_code="1234AB",
            house_number=1,
            session=session,
            loop=event_loop,
            request_timeout=1,
        )
        with pytest.raises(MeppelAfvalkalenderConnectionError):
            assert await tw._request("")


@pytest.mark.asyncio
async def test_http_error400(event_loop, aresponses):
    """Test HTTP 404 response handling."""
    aresponses.add(
        API_HOST,
        API_BASE_URI,
        "POST",
        aresponses.Response(text="OMG PUPPIES!", status=404),
    )

    async with aiohttp.ClientSession(loop=event_loop) as session:
        tw = MeppelAfvalkalender(
            post_code="1234AB", house_number=1, session=session, loop=event_loop
        )
        with pytest.raises(MeppelAfvalkalenderError):
            assert await tw._request("")


@pytest.mark.asyncio
async def test_http_error500(event_loop, aresponses):
    """Test HTTP 500 response handling."""
    aresponses.add(
        API_HOST,
        API_BASE_URI,
        "POST",
        aresponses.Response(
            body=b'{"status":"nok"}',
            status=500,
            headers={"Content-Type": "application/json"},
        ),
    )

    async with aiohttp.ClientSession(loop=event_loop) as session:
        tw = MeppelAfvalkalender(
            post_code="1234AB", house_number=1, session=session, loop=event_loop
        )
        with pytest.raises(MeppelAfvalkalenderError):
            assert await tw._request("")


@pytest.mark.asyncio
async def test_unique_id(event_loop, aresponses):
    """Test request of a unique address identifier."""
    aresponses.add(
        API_HOST,
        "{}FetchAdress".format(API_BASE_URI),
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"dataList": [{"UniqueId": "12345"}]}',
        ),
    )
    async with aiohttp.ClientSession(loop=event_loop) as session:
        tw = MeppelAfvalkalender(
            post_code="1234AB", house_number=1, session=session, loop=event_loop
        )
        unique_id = await tw.unique_id()
        assert unique_id == "12345"


@pytest.mark.asyncio
async def test_invalid_address(event_loop, aresponses):
    """Test request of invalid address information."""
    aresponses.add(
        API_HOST,
        "{}FetchAdress".format(API_BASE_URI),
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"dataList": []}',
        ),
    )
    async with aiohttp.ClientSession(loop=event_loop) as session:
        tw = MeppelAfvalkalender(
            post_code="1234AB", house_number=1, session=session, loop=event_loop
        )
        with pytest.raises(MeppelAfvalkalenderAddressError):
            assert await tw.unique_id()


@pytest.mark.asyncio
async def test_update(event_loop, aresponses):
    """Test request for updating data from Meppel Afvalkalender."""
    aresponses.add(
        API_HOST,
        "{}FetchAdress".format(API_BASE_URI),
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"dataList": [{"UniqueId": "12345"}]}',
        ),
    )
    aresponses.add(
        API_HOST,
        "{}GetCalendar".format(API_BASE_URI),
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=json.dumps(
                {
                    "dataList": [
                        {
                            "pickupDates": [
                                "2019-07-19T00:00:00",
                                "2019-07-20T00:00:00",
                            ],
                            "_pickupTypeText": "GREEN",
                        },
                        {
                            "pickupDates": ["2019-07-21T00:00:00"],
                            "_pickupTypeText": "GREY",
                        },
                        {
                            "pickupDates": ["2019-07-22T00:00:00"],
                            "_pickupTypeText": "PAPER",
                        },
                        {"pickupDates": [], "_pickupTypeText": "PACKAGES"},
                    ]
                }
            ),
        ),
    )

    async with aiohttp.ClientSession(loop=event_loop) as session:
        tw = MeppelAfvalkalender(
            post_code="1234AB", house_number=1, session=session, loop=event_loop
        )
        await tw.update()
        pickup = await tw.next_pickup(WASTE_TYPE_NON_RECYCLABLE)
        assert pickup == datetime(2019, 7, 21, 0, 0)
        pickup = await tw.next_pickup(WASTE_TYPE_ORGANIC)
        assert pickup == datetime(2019, 7, 19, 0, 0)
        pickup = await tw.next_pickup(WASTE_TYPE_PAPER)
        assert pickup == datetime(2019, 7, 22, 0, 0)
        pickup = await tw.next_pickup(WASTE_TYPE_PLASTIC)
        assert pickup is None
