from __future__ import annotations

from collections.abc import Awaitable, Callable
from urllib.parse import urlsplit

from starlette.responses import JSONResponse


ASGIApp = Callable[..., Awaitable[None]]
MAX_REQUEST_BODY_BYTES = 1_048_576
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _origin(value: str, *, allow_path: bool = False) -> str | None:
    try:
        parsed = urlsplit(value.strip())
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
            return None
        if parsed.username is not None or parsed.password is not None:
            return None
        if not allow_path and (parsed.path not in {"", "/"} or parsed.query or parsed.fragment):
            return None
        hostname = parsed.hostname.lower()
        if ":" in hostname and not hostname.startswith("["):
            hostname = f"[{hostname}]"
        port = parsed.port
        default_port = 443 if parsed.scheme.lower() == "https" else 80
        authority = hostname if port in {None, default_port} else f"{hostname}:{port}"
        return f"{parsed.scheme.lower()}://{authority}"
    except (TypeError, ValueError):
        return None


class ApplicationSecurityMiddleware:
    # API request limits, unsafe-method origin checks, and response headers.

    def __init__(
        self,
        app: ASGIApp,
        *,
        settings: object,
        max_request_body_bytes: int = MAX_REQUEST_BODY_BYTES,
    ) -> None:
        self.app = app
        self.settings = settings
        self.max_request_body_bytes = max_request_body_bytes

    def _allowed_origins(self, scope: dict, headers: dict[bytes, bytes]) -> set[str]:
        allowed: set[str] = set()
        configured_origin = _origin(str(getattr(self.settings, "frontend_base_url", "")), allow_path=True)
        if configured_origin:
            allowed.add(configured_origin)

        host = headers.get(b"x-forwarded-host", headers.get(b"host"))
        scheme = headers.get(b"x-forwarded-proto")
        if host:
            host_value = host.decode("latin-1").split(",", 1)[0].strip()
            scheme_value = (
                scheme.decode("latin-1").split(",", 1)[0].strip()
                if scheme
                else str(scope.get("scheme", "http"))
            )
            current_origin = _origin(f"{scheme_value}://{host_value}")
            if current_origin:
                allowed.add(current_origin)

        app_env = str(getattr(self.settings, "app_env", "development")).strip().lower()
        if app_env in {"development", "dev", "local"}:
            allowed.update({"http://127.0.0.1:3000", "http://localhost:3000"})
        return allowed

    @staticmethod
    def _request_origin(headers: dict[bytes, bytes]) -> tuple[bool, str | None]:
        origin_header = headers.get(b"origin")
        if origin_header is not None:
            return True, _origin(origin_header.decode("latin-1"))
        referer_header = headers.get(b"referer")
        if referer_header is not None:
            return True, _origin(referer_header.decode("latin-1"), allow_path=True)
        return False, None

    async def _respond(self, scope, receive, send, *, status_code: int, detail: str) -> None:
        response = JSONResponse({"detail": detail}, status_code=status_code)
        await response(scope, receive, send)

    async def __call__(self, scope, receive, send) -> None:
        async def send_with_security_headers(message: dict) -> None:
            if message["type"] == "http.response.start":
                response_headers = list(message.get("headers", []))
                present = {name.lower() for name, _ in response_headers}
                safe_headers = (
                    (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"strict-origin-when-cross-origin"),
                    (b"cache-control", b"no-store"),
                )
                for name, value in safe_headers:
                    if name not in present:
                        response_headers.append((name, value))
                message = {**message, "headers": response_headers}
            await send(message)

        if scope["type"] != "http":
            await self.app(scope, receive, send_with_security_headers)
            return

        headers = {name.lower(): value for name, value in scope.get("headers", [])}
        if scope.get("method", "GET").upper() in UNSAFE_METHODS:
            source_present, source_origin = self._request_origin(headers)
            if source_present and (
                source_origin is None or source_origin not in self._allowed_origins(scope, headers)
            ):
                await self._respond(
                    scope,
                    receive,
                    send_with_security_headers,
                    status_code=403,
                    detail="ORIGIN_NOT_ALLOWED",
                )
                return

            content_length = headers.get(b"content-length")
            if content_length:
                try:
                    if int(content_length) > self.max_request_body_bytes:
                        await self._respond(
                            scope,
                            receive,
                            send_with_security_headers,
                            status_code=413,
                            detail="REQUEST_BODY_TOO_LARGE",
                        )
                        return
                except ValueError:
                    pass

            messages: list[dict] = []
            received_size = 0
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                messages.append(message)
                if message["type"] == "http.request":
                    received_size += len(message.get("body", b""))
                    if received_size > self.max_request_body_bytes:
                        await self._respond(
                            scope,
                            receive,
                            send_with_security_headers,
                            status_code=413,
                            detail="REQUEST_BODY_TOO_LARGE",
                        )
                        return
                    if not message.get("more_body", False):
                        break

            message_index = 0

            async def replay_receive():
                nonlocal message_index
                if message_index < len(messages):
                    message = messages[message_index]
                    message_index += 1
                    return message
                return await receive()

            await self.app(scope, replay_receive, send_with_security_headers)
            return

        await self.app(scope, receive, send_with_security_headers)
