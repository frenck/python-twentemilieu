# pylint: disable=W0621
"""Asynchronous Python client for the Twente Milieu API."""

import asyncio

from twentemilieu import TwenteMilieu, WasteType


async def main():
    """Show example on stats from Twente Milieu."""
    async with TwenteMilieu(post_code="7545KR", house_number=175) as twente:
        print(twente)
        unique_id = await twente.unique_id()
        print("Unique Address ID:", unique_id)
        pickups = await twente.update()

        print("Next pickup for Organic:", pickups.get(WasteType.ORGANIC))
        print("Next pickup for Packages:", pickups.get(WasteType.PACKAGES))
        print("Next pickup for Paper:", pickups.get(WasteType.PAPER))
        print("Next pickup for Non-recyclable:", pickups.get(WasteType.NON_RECYCLABLE))
        print("Next pickup for Christmas Tree:", pickups.get(WasteType.TREE))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
