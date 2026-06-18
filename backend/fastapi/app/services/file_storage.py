from __future__ import annotations

from io import BytesIO
import os
from pathlib import Path
from urllib.parse import urlparse

from app.config import settings


def is_blob_uri(uri: str | None) -> bool:
    return bool(uri and uri.startswith("azure://"))


def _normalize_blob_name(blob_name: str) -> str:
    return blob_name.replace("\\", "/").lstrip("/")


def _azure_container_client():
    if not settings.AZURE_APP_STORAGE_CONNECTION_STRING:
        raise RuntimeError("AZURE_APP_STORAGE_CONNECTION_STRING is required for Azure Blob storage")

    from azure.storage.blob import BlobServiceClient

    service_client = BlobServiceClient.from_connection_string(
        settings.AZURE_APP_STORAGE_CONNECTION_STRING
    )
    return service_client.get_container_client(settings.AZURE_APP_STORAGE_CONTAINER)


def _parse_azure_uri(uri: str) -> tuple[str, str]:
    parsed = urlparse(uri)
    if parsed.scheme != "azure" or not parsed.netloc or not parsed.path:
        raise ValueError(f"Invalid Azure artifact URI: {uri}")
    return parsed.netloc, parsed.path.lstrip("/")


def _local_path(relative_path: str) -> Path:
    return Path(settings.APP_STORAGE_LOCAL_ROOT) / relative_path


def store_bytes(data: bytes, relative_path: str, content_type: str | None = None) -> str:
    relative_path = _normalize_blob_name(relative_path)

    if settings.APP_STORAGE_BACKEND == "azure_blob":
        from azure.storage.blob import ContentSettings

        container = _azure_container_client()
        content_settings = ContentSettings(content_type=content_type) if content_type else None
        container.upload_blob(
            name=relative_path,
            data=data,
            overwrite=True,
            content_settings=content_settings,
        )
        return f"azure://{settings.AZURE_APP_STORAGE_CONTAINER}/{relative_path}"

    target = _local_path(relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return str(target)


async def store_upload(file, relative_path: str) -> str:
    return store_bytes(
        await file.read(),
        relative_path=relative_path,
        content_type=getattr(file, "content_type", None),
    )


def store_dataframe_csv(df, relative_path: str) -> str:
    return store_bytes(
        df.to_csv(index=False).encode("utf-8"),
        relative_path=relative_path,
        content_type="text/csv",
    )


def exists(uri: str | None) -> bool:
    if not uri:
        return False

    if is_blob_uri(uri):
        if not settings.AZURE_APP_STORAGE_CONNECTION_STRING:
            return False

        container_name, blob_name = _parse_azure_uri(uri)
        if container_name != settings.AZURE_APP_STORAGE_CONTAINER:
            raise ValueError(f"Unexpected artifact container: {container_name}")
        return _azure_container_client().get_blob_client(blob_name).exists()

    return os.path.exists(uri)


def read_bytes(uri: str) -> bytes:
    if is_blob_uri(uri):
        container_name, blob_name = _parse_azure_uri(uri)
        if container_name != settings.AZURE_APP_STORAGE_CONTAINER:
            raise ValueError(f"Unexpected artifact container: {container_name}")
        return _azure_container_client().download_blob(blob_name).readall()

    return Path(uri).read_bytes()


def open_binary(uri: str) -> BytesIO:
    return BytesIO(read_bytes(uri))
