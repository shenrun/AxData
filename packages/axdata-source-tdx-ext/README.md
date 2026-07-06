# axdata-source-tdx-ext

TDX extended-market source Provider for AxData.

This package validates the AxData Provider protocol with the TDX extended-market interfaces: futures, options, funds, bonds, FX, and macro-style extended-market data. It exposes the `tdx_ext` interface group through the `axdata.providers` entry point and embeds `axdata-provider.json` as package data.

The current implementation reuses AxData core's existing TDX extended-market catalog, local cache parser, short-connection client, pool logic, and adapter while the plugin protocol is being stabilized. When installed as part of the official `axdata` package, this Provider is available by default and can still be disabled through AxData plugin configuration. Full extraction of the extended-market client/cache implementation is a later phase.
