# -*- coding: utf-8 -*-
"""Twente Milieu constants."""

API_HOST = "wasteapi.2go-mobile.com"
API_BASE_URI = "/api/"
API_COMPANY_CODE = "8d97bb56-5afd-4cbc-a651-b4f7314264b4"

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
