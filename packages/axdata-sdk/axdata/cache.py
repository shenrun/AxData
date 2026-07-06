"""Local cache API placeholders for AxData."""


def download(*args, **kwargs):
    """Placeholder for a future local cache download implementation."""

    raise NotImplementedError(
        "axdata.download(...) is reserved for the future local cache workflow. "
        "It will download API data into a local cache when implemented."
    )


def get(*args, **kwargs):
    """Placeholder for a future local cache read implementation."""

    raise NotImplementedError(
        "axdata.get(...) is reserved for the future local cache workflow. "
        "It will read data from the local cache when implemented."
    )
