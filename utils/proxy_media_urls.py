import json
import os
import uuid as uuid_module

import requests

MEDIA_EXTENSIONS = frozenset({
    'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp',
    'mp4', 'mov', 'avi', 'webm',
    'mp3', 'wav', 'ogg', 'flac', 'm4a',
    'pdf',
})

_CONTENT_TYPE_TO_EXT = {
    'image/png': 'png',
    'image/jpeg': 'jpg',
    'image/gif': 'gif',
    'image/webp': 'webp',
    'image/svg+xml': 'svg',
    'image/bmp': 'bmp',
    'video/mp4': 'mp4',
    'video/webm': 'webm',
    'video/quicktime': 'mov',
    'audio/mpeg': 'mp3',
    'audio/wav': 'wav',
    'audio/ogg': 'ogg',
    'audio/flac': 'flac',
    'audio/mp4': 'm4a',
    'application/pdf': 'pdf',
}


def _is_media_url(value: str) -> bool:
    """Return True if the string is an http(s) URL pointing to a known media file."""
    if not isinstance(value, str) or not value.startswith(('http://', 'https://')):
        return False
    # Strip query-string and fragment before checking extension
    path = value.split('?')[0].split('#')[0]
    ext = path.rsplit('.', 1)[-1].lower() if '.' in path else ''
    return ext in MEDIA_EXTENSIONS


def _download_url(url: str, upload_dir: str) -> str | None:
    """
    Download *url* into *upload_dir*.

    Returns the generated filename on success, or None if the download fails.
    The extension is inferred from (in order of priority):
      1. Content-Type response header
      2. Content-Disposition response header
      3. The URL path itself
    """
    try:
        os.makedirs(upload_dir, exist_ok=True)

        path = url.split('?')[0].split('#')[0]
        ext = path.rsplit('.', 1)[-1].lower() if '.' in path else 'bin'

        resp = requests.get(url, timeout=60)
        resp.raise_for_status()

        # Refine extension from Content-Disposition header
        cd = resp.headers.get('Content-Disposition', '')
        if '.' in cd:
            cd_ext = cd.rsplit('.', 1)[-1].strip().strip('"').lower()
            if cd_ext in MEDIA_EXTENSIONS:
                ext = cd_ext

        # Refine extension from Content-Type header (highest priority)
        ct = resp.headers.get('Content-Type', '').split(';')[0].strip()
        if ct in _CONTENT_TYPE_TO_EXT:
            ext = _CONTENT_TYPE_TO_EXT[ct]

        file_name = f'{uuid_module.uuid4()}.{ext}'
        file_path = os.path.join(upload_dir, file_name)
        with open(file_path, 'wb') as f:
            f.write(resp.content)

        return file_name
    except Exception as e:
        print(f'[proxy_media] Failed to download {url}: {e}')
        return None


def _process_value(value, upload_dir: str, base_url: str):
    """
    Recursively walk *value* (dict / list / str / other).

    Strings are handled in two steps:
      1. If the string looks like a JSON object/array, parse it, recurse, and
         re-serialise — this handles fields like ``resultJson`` or ``param``
         that arrive as JSON-encoded strings.
      2. If the string is a bare media URL, download it and replace with the
         proxied server URL.
    """
    if isinstance(value, dict):
        return {k: _process_value(v, upload_dir, base_url) for k, v in value.items()}

    if isinstance(value, list):
        return [_process_value(item, upload_dir, base_url) for item in value]

    if isinstance(value, str):
        stripped = value.strip()

        # Try to parse embedded JSON strings before checking for a bare URL
        if stripped.startswith(('{', '[')):
            try:
                parsed = json.loads(value)
                processed = _process_value(parsed, upload_dir, base_url)
                return json.dumps(processed, ensure_ascii=False)
            except (json.JSONDecodeError, ValueError):
                pass

        if _is_media_url(value):
            file_name = _download_url(value, upload_dir)
            if file_name:
                return f'{base_url}/uploads/{file_name}'

    return value


def proxy_media_in_result(result_data: dict, upload_dir: str, base_url: str) -> dict:
    """
    Scan *result_data* recursively for media URLs, download each one into
    *upload_dir*, and return a copy of the data with every URL replaced by a
    local proxied URL of the form ``{base_url}/uploads/<filename>``.

    JSON-encoded string values (e.g. ``resultJson``, ``param``) are parsed,
    processed in-place, and re-serialised so that nested URLs are also proxied.

    :param result_data: The raw result dict received from the external service.
    :param upload_dir:  Absolute path to the directory where files are stored.
    :param base_url:    Server base URL, e.g. ``https://queue.api2app.org``.
    :returns: A new dict with all media URLs replaced by proxied equivalents.
    """
    return _process_value(result_data, upload_dir, base_url)
