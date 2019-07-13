# -*- coding: utf-8 -*-
# pylint: disable=W0621
"""Asynchronous Python client for the Twente Milieu API."""

import asyncio

from twentemilieu import (
    WASTE_TYPE_NON_RECYCLABLE,
    WASTE_TYPE_ORGANIC,
    WASTE_TYPE_PAPER,
    WASTE_TYPE_PLASTIC,
    TwenteMilieu,
)


async def main(loop):
    """Show example on stats from Twente Milieu."""
    async with TwenteMilieu(post_code="7545KR", house_number=175, loop=loop) as tw:
        print(tw)
        unique_id = await tw.unique_id()
        print("Unique Address ID:", unique_id)
        await tw.update()
        pickup = await tw.next_pickup(WASTE_TYPE_ORGANIC)
        print("Next pickup for Organic:", pickup)
        pickup = await tw.next_pickup(WASTE_TYPE_PLASTIC)
        print("Next pickup for Plastic:", pickup)
        pickup = await tw.next_pickup(WASTE_TYPE_PAPER)
        print("Next pickup for Paper:", pickup)
        pickup = await tw.next_pickup(WASTE_TYPE_NON_RECYCLABLE)
        print("Next pickup for Non-recyclable:", pickup)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
