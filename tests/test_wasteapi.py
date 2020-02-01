# -*- coding: utf-8 -*-
"""Tests for `wasteapi.wasteapi`."""
import asyncio
import json
from datetime import datetime

import aiohttp
import pytest
from wasteapi import WasteApi
from wasteapi.__version__ import __version__
from wasteapi.const import (
    API_BASE_URI,
    API_HOST,
    COMPANY_CODE_TWENTEMILIEU,
    WASTE_TYPE_NON_RECYCLABLE,
    WASTE_TYPE_ORGANIC,
    WASTE_TYPE_PAPER,
    WASTE_TYPE_PLASTIC,
)
from wasteapi.exceptions import (
    WasteApiAddressError,
    WasteApiConnectionError,
    WasteApiError,
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
        wa = WasteApi(
            company_code=COMPANY_CODE_TWENTEMILIEU,
            post_code="1234AB",
            house_number="1",
            session=session,
            loop=event_loop,
        )
        response = await wa._request("")
        assert response["status"] == "ok"


@pytest.mark.asyncio
async def test_text_request(event_loop, aresponses):
    """Test non JSON response is handled correctly."""
    aresponses.add(
        API_HOST, API_BASE_URI, "POST", aresponses.Response(status=200, text="OK")
    )
    async with aiohttp.ClientSession(loop=event_loop) as session:
        wa = WasteApi(
            company_code=COMPANY_CODE_TWENTEMILIEU,
            post_code="1234AB",
            house_number="1",
            session=session,
            loop=event_loop,
        )
        response = await wa._request("")
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
    async with WasteApi(
        company_code=COMPANY_CODE_TWENTEMILIEU,
        post_code="1234AB",
        house_number="1",
        loop=event_loop,
    ) as wa:
        response = await wa._request("")
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
    async with WasteApi(
        company_code=COMPANY_CODE_TWENTEMILIEU, post_code="1234AB", house_number="1"
    ) as wa:
        response = await wa._request("")
        assert response["status"] == "ok"


@pytest.mark.asyncio
async def test_request_user_agent(event_loop, aresponses):
    """Test if client is sending correct user agent headers."""
    # Handle to run asserts on request in
    async def response_handler(request):
        assert request.headers["User-Agent"] == "PythonWasteAPI/{}".format(__version__)
        return aresponses.Response(text="TEDDYBEAR", status=200)

    aresponses.add(API_HOST, API_BASE_URI, "POST", response_handler)

    async with aiohttp.ClientSession(loop=event_loop) as session:
        wa = WasteApi(
            company_code=COMPANY_CODE_TWENTEMILIEU,
            post_code="1234AB",
            house_number="1",
            session=session,
            loop=event_loop,
        )
        await wa._request("")


@pytest.mark.asyncio
async def test_request_custom_user_agent(event_loop, aresponses):
    """Test if client is sending correct user agent headers."""
    # Handle to run asserts on request in
    async def response_handler(request):
        assert request.headers["User-Agent"] == "LoremIpsum/1.0"
        return aresponses.Response(text="TEDDYBEAR", status=200)

    aresponses.add(API_HOST, API_BASE_URI, "POST", response_handler)

    async with aiohttp.ClientSession(loop=event_loop) as session:
        wa = WasteApi(
            company_code=COMPANY_CODE_TWENTEMILIEU,
            post_code="1234AB",
            house_number="1",
            session=session,
            loop=event_loop,
            user_agent="LoremIpsum/1.0",
        )
        await wa._request("")


@pytest.mark.asyncio
async def test_timeout(event_loop, aresponses):
    """Test request timeout from WasteAPI."""
    # Faking a timeout by sleeping
    async def response_handler(_):
        await asyncio.sleep(2)
        return aresponses.Response(body="Goodmorning!")

    aresponses.add(API_HOST, API_BASE_URI, "POST", response_handler)

    async with aiohttp.ClientSession(loop=event_loop) as session:
        wa = WasteApi(
            company_code=COMPANY_CODE_TWENTEMILIEU,
            post_code="1234AB",
            house_number="1",
            session=session,
            loop=event_loop,
            request_timeout=1,
        )
        with pytest.raises(WasteApiConnectionError):
            assert await wa._request("")


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
        wa = WasteApi(
            company_code=COMPANY_CODE_TWENTEMILIEU,
            post_code="1234AB",
            house_number="1",
            session=session,
            loop=event_loop,
        )
        with pytest.raises(WasteApiError):
            assert await wa._request("")


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
        wa = WasteApi(
            company_code=COMPANY_CODE_TWENTEMILIEU,
            post_code="1234AB",
            house_number="1",
            session=session,
            loop=event_loop,
        )
        with pytest.raises(WasteApiError):
            assert await wa._request("")


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
        wa = WasteApi(
            company_code=COMPANY_CODE_TWENTEMILIEU,
            post_code="1234AB",
            house_number="1",
            session=session,
            loop=event_loop,
        )
        unique_id = await wa.unique_id()
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
        wa = WasteApi(
            company_code=COMPANY_CODE_TWENTEMILIEU,
            post_code="1234AB",
            house_number="1",
            session=session,
            loop=event_loop,
        )
        with pytest.raises(WasteApiAddressError):
            assert await wa.unique_id()


@pytest.mark.asyncio
async def test_update(event_loop, aresponses):
    """Test request for updating data from WasteAPI."""
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
        wa = WasteApi(
            company_code=COMPANY_CODE_TWENTEMILIEU,
            post_code="1234AB",
            house_number="1",
            session=session,
            loop=event_loop,
        )
        await wa.update()
        pickup = await wa.next_pickup(WASTE_TYPE_NON_RECYCLABLE)
        assert pickup == datetime(2019, 7, 21, 0, 0)
        pickup = await wa.next_pickup(WASTE_TYPE_ORGANIC)
        assert pickup == datetime(2019, 7, 19, 0, 0)
        pickup = await wa.next_pickup(WASTE_TYPE_PAPER)
        assert pickup == datetime(2019, 7, 22, 0, 0)
        pickup = await wa.next_pickup(WASTE_TYPE_PLASTIC)
        assert pickup is None
