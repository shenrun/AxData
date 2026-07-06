# axdata-source-cninfo

Cninfo announcement source Provider for AxData.

This package validates the AxData plugin protocol with a multi-interface public HTTP source. It exposes `cninfo_announcements` and `cninfo_announcement_detail` through the `axdata.providers` entry point and embeds `axdata-provider.json` as package data.

The current implementation reuses AxData core's existing Cninfo adapter while the plugin protocol is being stabilized. When installed through the official `axdata` package, Cninfo capability is part of the default source set. If this package is installed independently as a plugin package, AxData plugin configuration still controls whether it participates in routing.
