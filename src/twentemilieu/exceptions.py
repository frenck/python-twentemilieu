"""Exceptions for Twente Milieu."""


class TwenteMilieuError(Exception):
    """Generic Twente Milieu exception."""


class TwenteMilieuConnectionError(TwenteMilieuError):
    """Twente Milieu connection exception."""


class TwenteMilieuAddressError(TwenteMilieuError):
    """Twente Milieu unknown address exception."""
