"""TDX file resource API."""

from __future__ import annotations

from axdata_source_tdx._tdx_wire._request_defaults import DEFAULT_FILE_CHUNK_SIZE

from .base import ApiBase


class ResourceApi(ApiBase):
    def download_chunk(self, path: str, *, offset: int = 0, size: int = DEFAULT_FILE_CHUNK_SIZE):
        return self._execute("file_content", path=path, offset=offset, size=size)

    def download_file(
        self,
        path: str,
        *,
        chunk_size: int = DEFAULT_FILE_CHUNK_SIZE,
        max_bytes: int | None = None,
    ) -> bytes:
        offset = 0
        chunks: list[bytes] = []
        while True:
            if max_bytes is not None and offset >= max_bytes:
                break
            size = chunk_size
            if max_bytes is not None:
                size = min(size, max_bytes - offset)
            chunk = self.download_chunk(path, offset=offset, size=size)
            chunks.append(chunk.content)
            offset += chunk.chunk_len
            if chunk.is_last or chunk.chunk_len == 0:
                break
        return b"".join(chunks)
