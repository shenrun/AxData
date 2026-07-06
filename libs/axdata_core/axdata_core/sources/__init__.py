"""Source interface catalog registry."""

from __future__ import annotations

from .base import RequestExample, RequestField, RequestParameter, SourceRequestInterface

__all__ = [
    "RequestExample",
    "RequestField",
    "RequestParameter",
    "SourceRequestInterface",
    "get_request_interface",
    "list_request_interface_dicts",
    "list_request_interface_names",
    "list_request_interfaces",
]


def list_request_interfaces():
    from .catalog import list_request_interfaces as value

    return value()


def list_request_interface_names():
    from .catalog import list_request_interface_names as value

    return value()


def list_request_interface_dicts():
    from .catalog import list_request_interface_dicts as value

    return value()


def get_request_interface(name: str):
    from .catalog import get_request_interface as value

    return value(name)
