# axdata-source-tdx

TDX quote source Provider for AxData.

This package provides the TDX data source plugin shape for AxData. It exposes the ordinary TDX quote interfaces through the `axdata.providers` entry point and embeds `axdata-provider.json` as package data.

The current implementation owns the TDX catalog, adapter, wire client, server configuration, connection options, F10 helpers, caches, and downloader profile projection. When installed as part of the official `axdata` package, this Provider is available by default and can still be disabled through AxData plugin configuration. If this package is missing or explicitly disabled, AxData reports that the TDX plugin should be checked instead of running a core fallback.
