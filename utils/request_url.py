"""
Helpers for resolving the public-facing base URL of an incoming request.

When the application runs behind a reverse proxy (nginx, traefik, etc.) that
terminates TLS, ``request.url.scheme`` reports the *internal* scheme used
between the proxy and the app (usually ``http``) instead of the *external*
scheme seen by the client (often ``https``). The same problem applies to the
host name and port when the proxy listens on a different address than the
upstream application.

The standard way for proxies to communicate the original request information
to the upstream service is via the ``Forwarded`` (RFC 7239) and
``X-Forwarded-*`` headers. This module looks at those headers first and
falls back to the values stored on ``request.url`` only when the headers are
absent.

Note that you should also start uvicorn with ``--proxy-headers`` (and an
appropriate ``--forwarded-allow-ips`` value) so that Starlette itself sees
the correct scheme/host. The helpers below stay correct in either case and
are safe to use even when the proxy is not configured to forward those
headers (in that case the behaviour is identical to the previous inline
``f"{request.url.scheme}://{request.url.hostname}"`` construction).
"""

from __future__ import annotations

from typing import Optional, Tuple

from fastapi import Request


_DEFAULT_PORTS = {'http': 80, 'https': 443}

_PROXY_SCHEME_HEADERS = (
    'x-forwarded-proto',
    'x-forwarded-protocol',
    'x-url-scheme',
    'x-forwarded-ssl',
    'front-end-https',
    'forwarded',
)

_PROXY_HOST_HEADERS = ('x-forwarded-host', 'forwarded')
_PROXY_PORT_HEADERS = ('x-forwarded-port', 'x-forwarded-host', 'forwarded')


def _parse_forwarded_header(forwarded: str) -> dict:
    """Parse the first element of an RFC 7239 ``Forwarded`` header.

    Only the first hop is taken into account because that is the proxy
    closest to the client and therefore the most trustworthy source of the
    original request information when the proxy is under our control.
    """
    first = forwarded.split(',', 1)[0]
    parts = {}
    for chunk in first.split(';'):
        if '=' not in chunk:
            continue
        key, _, value = chunk.strip().partition('=')
        parts[key.strip().lower()] = value.strip().strip('"')
    return parts


def _scheme_from_headers(request: Request) -> Optional[str]:
    """Return the scheme advertised by proxy headers, or ``None``."""
    headers = request.headers

    forwarded = headers.get('forwarded')
    if forwarded:
        proto = _parse_forwarded_header(forwarded).get('proto')
        if proto:
            return proto.lower()

    for header_name in ('x-forwarded-proto', 'x-forwarded-protocol', 'x-url-scheme'):
        value = headers.get(header_name)
        if value:
            return value.split(',', 1)[0].strip().lower()

    for header_name in ('x-forwarded-ssl', 'front-end-https'):
        value = headers.get(header_name)
        if value and value.strip().lower() == 'on':
            return 'https'

    return None


def _host_and_port_from_headers(request: Request) -> Tuple[Optional[str], Optional[int]]:
    """Return ``(host, port)`` advertised by proxy headers (each may be ``None``)."""
    headers = request.headers
    host: Optional[str] = None
    port: Optional[int] = None

    forwarded = headers.get('forwarded')
    if forwarded:
        forwarded_host = _parse_forwarded_header(forwarded).get('host')
        if forwarded_host:
            if ':' in forwarded_host:
                host_part, _, port_part = forwarded_host.rpartition(':')
                host = host_part
                try:
                    port = int(port_part)
                except ValueError:
                    port = None
            else:
                host = forwarded_host

    if host is None:
        forwarded_host = headers.get('x-forwarded-host')
        if forwarded_host:
            first_hop = forwarded_host.split(',', 1)[0].strip()
            if ':' in first_hop:
                host_part, _, port_part = first_hop.rpartition(':')
                host = host_part
                if port is None:
                    try:
                        port = int(port_part)
                    except ValueError:
                        port = None
            else:
                host = first_hop

    forwarded_port = headers.get('x-forwarded-port')
    if forwarded_port:
        try:
            port = int(forwarded_port.split(',', 1)[0].strip())
        except ValueError:
            pass

    return host, port


def _has_proxy_signal(request: Request) -> bool:
    """Return ``True`` if any proxy header is present on *request*.

    When that is the case we trust the proxy headers exclusively for the
    public-facing URL components, because the values on ``request.url`` are
    the internal upstream address (e.g. ``http://127.0.0.1:8002``) and would
    otherwise leak into URLs returned to clients.
    """
    return any(header in request.headers for header in _PROXY_SCHEME_HEADERS + _PROXY_HOST_HEADERS + _PROXY_PORT_HEADERS)


def get_request_scheme(request: Request) -> str:
    """Return the original request scheme (``http`` or ``https``).

    Order of precedence:
      1. ``Forwarded: proto=...`` (RFC 7239)
      2. ``X-Forwarded-Proto``
      3. ``X-Forwarded-Protocol`` / ``X-Url-Scheme`` (used by some proxies)
      4. ``X-Forwarded-Ssl: on`` / ``Front-End-Https: on``
      5. ``request.url.scheme``
    """
    return _scheme_from_headers(request) or request.url.scheme


def get_request_host(request: Request) -> Optional[str]:
    """Return the original host name (without port) of the request."""
    host, _ = _host_and_port_from_headers(request)
    if host:
        return host
    return request.url.hostname


def get_request_port(request: Request) -> Optional[int]:
    """Return the original port of the request, or ``None`` if it should be
    omitted from the URL (e.g. the default port for the resolved scheme).

    When proxy headers are present, the internal upstream port from
    ``request.url`` is intentionally ignored, because it represents the
    address between the proxy and this app rather than the public-facing
    port the client connected to.
    """
    _, port = _host_and_port_from_headers(request)
    if port is not None:
        return port
    if _has_proxy_signal(request):
        return None
    return request.url.port


def get_base_url(request: Request) -> str:
    """Return the public base URL (``scheme://host[:port]``) for *request*.

    Uses ``X-Forwarded-*`` / ``Forwarded`` headers when present so that URLs
    built for clients (download links, webhook callback URLs, etc.) match
    what the user originally typed in the browser instead of the internal
    address used between the reverse proxy and this application.
    """
    scheme = get_request_scheme(request)
    host = get_request_host(request) or ''
    port = get_request_port(request)

    base_url = f'{scheme}://{host}'
    if port is not None and port != _DEFAULT_PORTS.get(scheme):
        base_url += f':{port}'
    return base_url
