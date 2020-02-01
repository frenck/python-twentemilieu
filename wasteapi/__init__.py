# -*- coding: utf-8 -*-
"""Asynchronous Python client for WasteAPI."""

from .const import (  # noqa
    WASTE_TYPE_NON_RECYCLABLE,
    WASTE_TYPE_ORGANIC,
    WASTE_TYPE_PAPER,
    WASTE_TYPE_PLASTIC,
)
from .wasteapi import (  # noqa
    WasteApi,
    WasteApiAddressError,
    WasteApiConnectionError,
    WasteApiError,
)
