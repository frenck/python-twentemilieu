# -*- coding: utf-8 -*-
"""Exceptions for Twente Milieu."""


class TwenteMilieuError(Exception):
    """Generic Twente Milieu exception."""

    pass


class TwenteMilieuConnectionError(TwenteMilieuError):
    """Twente Milieu connection exception."""

    pass


class TwenteMilieuAddressError(TwenteMilieuError):
    """Twente Milieu unknown address exception."""

    pass
