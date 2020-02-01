# -*- coding: utf-8 -*-
# pylint: disable=W0621
"""Asynchronous Python client for the WasteAPI."""

import asyncio

from wasteapi import (
    WASTE_TYPE_NON_RECYCLABLE,
    WASTE_TYPE_ORGANIC,
    WASTE_TYPE_PAPER,
    WASTE_TYPE_PLASTIC,
    WasteApi,
)
from wasteapi.const import COMPANY_CODE_AREA_REINIGING


async def main(loop):
    """Show example on stats from WasteAPI."""
    async with WasteApi(
        company_code=COMPANY_CODE_AREA_REINIGING,
        post_code="7815XG",
        house_number="32",
        loop=loop,
    ) as wa:

        print(wa)
        unique_id = await wa.unique_id()
        print("Unique Address ID:", unique_id)
        await wa.update()
        pickup = await wa.next_pickup(WASTE_TYPE_ORGANIC)
        print("Next pickup for Organic:", pickup)
        pickup = await wa.next_pickup(WASTE_TYPE_PLASTIC)
        print("Next pickup for Plastic:", pickup)
        pickup = await wa.next_pickup(WASTE_TYPE_PAPER)
        print("Next pickup for Paper:", pickup)
        pickup = await wa.next_pickup(WASTE_TYPE_NON_RECYCLABLE)
        print("Next pickup for Non-recyclable:", pickup)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
