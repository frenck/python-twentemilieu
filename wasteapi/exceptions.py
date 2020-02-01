# -*- coding: utf-8 -*-
"""Exceptions for WasteApi."""


class WasteApiError(Exception):
    """Generic WasteApi exception."""

    pass


class WasteApiConnectionError(WasteApiError):
    """WasteApi connection exception."""

    pass


class WasteApiAddressError(WasteApiError):
    """WasteApi unknown address exception."""

    pass
