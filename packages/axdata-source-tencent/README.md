# axdata-source-tencent

Tencent Finance source Provider for AxData.

This package is the first real Provider package shape used to validate the AxData plugin protocol. It exposes `tencent_realtime_snapshot` through the `axdata.providers` entry point and embeds `axdata-provider.json` as package data.

The current implementation reuses AxData core's existing Tencent adapter while the plugin protocol is being stabilized. When installed through the official `axdata` package, Tencent Finance capability is part of the default source set. If this package is installed independently as a plugin package, AxData plugin configuration still controls whether it participates in routing.
