from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    table: str = Field(description="AxData core/factor table name to query.")
    fields: str | list[str] | None = Field(
        default=None,
        description="Selected AxData fields. Accepts a comma-separated string or a list.",
    )
    columns: str | list[str] | None = Field(default=None, description="Alias for fields.")
    filters: dict[str, Any] | None = Field(
        default=None,
        description="Explicit exact-match filters. None values are ignored.",
    )
    params: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "SDK-style query parameters. start/start_date and end/end_date are treated as "
            "date ranges; remaining non-null values are merged into filters."
        ),
    )
    start_date: str | None = Field(default=None, description="Start date, YYYYMMDD or YYYY-MM-DD.")
    end_date: str | None = Field(default=None, description="End date, YYYYMMDD or YYYY-MM-DD.")
    start: str | None = Field(default=None, description="Alias for start_date.")
    end: str | None = Field(default=None, description="Alias for end_date.")
    limit: int | None = Field(default=1000, ge=1, le=100000, description="Maximum rows. Null disables the limit.")


class SourceRequest(BaseModel):
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Source-interface parameters.",
    )
    fields: str | list[str] | None = Field(
        default=None,
        description="Requested AxData fields.",
    )
    options: dict[str, Any] | None = Field(
        default=None,
        description="Execution options such as TDX connection pool settings. These do not change source-interface parameters.",
    )
    persist: bool = Field(
        default=False,
        description="Reserved for explicit collection jobs. Source requests never persist data.",
    )


class ProviderOverrideRequest(BaseModel):
    provider_id: str = Field(description="Provider id to route this interface to.")


class ApiTokenCreateRequest(BaseModel):
    name: str = Field(description="Human-readable token name, usually a device or script name.")


class RuntimeConfigUpdateRequest(BaseModel):
    api_host: str = Field(default="127.0.0.1", description="API host for the next API start.")
    api_port: int = Field(default=8666, ge=1, le=65535, description="API port for the next API start.")
    web_port: int = Field(default=8667, ge=1, le=65535, description="Local Web port for the next Web start.")


class TradeCalendarMaintenanceUpdateRequest(BaseModel):
    enabled: bool = Field(default=False, description="Whether daily trade-calendar maintenance is enabled.")
    time: str = Field(default="22:30", pattern=r"^\d{2}:\d{2}$", description="Local daily run time, HH:MM.")
    past_days: int = Field(default=30, ge=0, le=3650, description="Days before today to maintain.")
    future_days: int = Field(default=180, ge=0, le=3650, description="Days after today to maintain.")
    recheck_past_days: int = Field(default=30, ge=0, le=3650, description="Recent past days to refresh again.")


class PluginCollectorRunRequest(BaseModel):
    params: dict[str, Any] = Field(default_factory=dict, description="Collector run parameters.")
    fields: str | list[str] | None = Field(default=None, description="Selected fields to persist.")
    output_root: str | None = Field(default=None, description="Directory used as the downloader output root.")
    output_dir: str | None = Field(default=None, description="Final directory where output files are written.")
    formats: str | list[str] | None = Field(default=None, description="Output file formats.")
    collect_mode: str | None = Field(default=None, description="Collection mode.")
    connection_mode: str | None = Field(default=None, description="Downloader connection mode.")
    concurrency_mode: str | None = Field(default=None, description="Downloader concurrency preset mode.")
    connection_count: int | None = Field(default=None, description="Number of source connections/workers.")
    source_server_count: int | None = Field(default=None, description="Number of source servers to use.")
    connections_per_server: int | None = Field(default=None, description="Long connections per source server.")
    max_concurrent_tasks: int | None = Field(default=None, description="Maximum concurrent downloader tasks.")
    batch_size: int | None = Field(default=None, description="Downloader task batch size.")
    request_interval_ms: int | None = Field(default=None, description="Interval between source requests in milliseconds.")
    retry_count: int | None = Field(default=None, description="Retry count for source requests.")
    timeout_ms: int | None = Field(default=None, description="Per-request timeout in milliseconds.")
    async_job: bool = Field(default=False, description="Run as a background collector job.")
