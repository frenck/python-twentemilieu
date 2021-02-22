# -*- coding: utf-8 -*-
"""Exceptions for Meppel Afvalkalender."""


class MeppelAfvalkalenderError(Exception):
    """Generic Meppel Afvalkalender exception."""

    pass


class MeppelAfvalkalenderConnectionError(MeppelAfvalkalenderError):
    """Meppel Afvalkalender connection exception."""

    pass


class MeppelAfvalkalenderAddressError(MeppelAfvalkalenderError):
    """Meppel Afvalkalender unknown address exception."""

    pass
