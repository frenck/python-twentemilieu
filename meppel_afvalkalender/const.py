# -*- coding: utf-8 -*-
"""Meppel Afvalkalender constants."""

API_HOST = "wasteapi.ximmio.com"
API_BASE_URI = "/api/"
API_COMPANY_CODE = "b7a594c7-2490-4413-88f9-94749a3ec62a"

WASTE_TYPE_NON_RECYCLABLE = "Non-recyclable"
WASTE_TYPE_ORGANIC = "Organic"
WASTE_TYPE_PAPER = "Paper"
WASTE_TYPE_PLASTIC = "Plastic"

API_TO_WASTE_TYPE = {
    "GREEN": WASTE_TYPE_ORGANIC,
    "GREY": WASTE_TYPE_NON_RECYCLABLE,
    "PACKAGES": WASTE_TYPE_PLASTIC,
    "PAPER": WASTE_TYPE_PAPER,
}
