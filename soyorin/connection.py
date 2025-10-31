from soyorin.url import AboutUrlInfo
from soyorin.cache import FileCache
from typing import Dict
from typing import ClassVar
from datetime import datetime
from typing import Literal
from typing import Optional
from typing import TypedDict
from typing import NamedTuple
from socket import socket as Socket, AF_INET, SOCK_STREAM, IPPROTO_TCP
from io import BufferedReader
import ssl

from soyorin.url import URL, FileUrlInfo, DataUrlInfo, HttpUrlInfo
from soyorin.cache import Cache, BrowserCacheKey, BrowserCacheEntry


class HttpOptions(TypedDict):
    http_version: Optional[Literal["1.0", "1.1"]]


class ConnectionPoolCacheKey(NamedTuple):
    host: str
    port: int


class Connection:
    connection_pool: ClassVar[Dict[ConnectionPoolCacheKey, Socket]] = {}

    socket: Optional[Socket]
    http_options: HttpOptions
    browser_cache: Cache

    def __init__(
        self, http_options: Optional[HttpOptions] = None, cache: Optional[Cache] = None
    ):
        self.socket = None
        self.http_options = http_options or {"http_version": "1.0"}
        self.browser_cache = cache or FileCache()

    def __read_chunked_body(self, response: BufferedReader) -> bytes:
        body = b""
        while True:
            chunk_size_line = response.readline()
            chunk_size = int(chunk_size_line.decode("utf-8").strip(), 16)
            if chunk_size == 0:
                break
            chunk_data = response.read(chunk_size)
            body += chunk_data
            response.readline()  # 개행 문자 제거

        return body

    def __request_data(self, url_info: DataUrlInfo) -> str:
        return url_info.data

    def __request_file(self, url_info: FileUrlInfo) -> str:
        path = url_info.path or ""
        # On Windows, file URLs have paths like /C:/path/file.html
        # We need to remove the leading slash before the drive letter
        if len(path) > 2 and path[0] == "/" and path[2] == ":":
            path = path[1:]
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def __request_about(self, url_info: AboutUrlInfo) -> str:
        if url_info.path == "blank":
            return ""
        else:
            raise ValueError("Unsupported about: scheme")

    def __request_http(
        self, url_info: HttpUrlInfo, http_options: HttpOptions, redirect_count=20
    ) -> str:
        now = datetime.now()
        browser_cache_key = BrowserCacheKey.from_http_info(url_info)

        if browser_cache_key in self.browser_cache:
            cached_content = self.browser_cache.get(browser_cache_key)
            if cached_content:
                age = (
                    (now - cached_content.timestamp).total_seconds()
                    if cached_content.timestamp
                    else 0
                )

                if age >= cached_content.max_age:
                    self.browser_cache.delete(browser_cache_key)
                else:
                    return cached_content.content

        if http_options["http_version"] not in ["1.0", "1.1"]:
            raise ValueError("Unsupported HTTP version")

        if http_options["http_version"] == "1.1":
            key = ConnectionPoolCacheKey(host=url_info.host or "", port=url_info.port)
            if key in Connection.connection_pool:
                self.socket = Connection.connection_pool[key]

        response_headers = {}

        while True:
            if redirect_count < 0:
                raise RuntimeError("Maximum redirect limit reached")

            if self.socket is None:
                self.socket = Socket(
                    family=AF_INET, type=SOCK_STREAM, proto=IPPROTO_TCP
                )

            self.socket.connect((url_info.host, url_info.port))
            if url_info.scheme == "https":
                ctx = ssl.create_default_context()
                self.socket = ctx.wrap_socket(
                    self.socket, server_hostname=url_info.host
                )

            if http_options["http_version"] == "1.1":
                key = ConnectionPoolCacheKey(
                    host=url_info.host or "", port=url_info.port
                )
                if key not in Connection.connection_pool:
                    Connection.connection_pool[key] = self.socket

            request = f"GET {url_info.path} HTTP/{http_options['http_version']}\r\n"
            request += f"Host: {url_info.host}\r\n"

            if http_options["http_version"] == "1.1":
                request += "Connection: keep-alive\r\n"
            elif http_options["http_version"] == "1.0":
                request += "Connection: close\r\n"
            request += "User-Agent: soyorin/1.0\r\n"
            request += "Accept-Encoding: *\r\n"
            request += "\r\n"

            self.socket.send(request.encode("utf-8"))

            response = self.socket.makefile("rb", encoding="utf-8", newline="\r\n")
            statusline = response.readline().decode("utf-8")
            version, status, explanation = statusline.split(" ", 2)

            # Header 분석
            response_headers = {}
            while True:
                line = response.readline().decode("utf-8")
                if line == "\r\n":
                    break
                header, value = line.split(":", 1)
                response_headers[header.casefold()] = value.strip()

            # Redirect 처리
            if status.startswith("3") and "location" in response_headers:
                if response_headers["location"].startswith(
                    "http://"
                ) or response_headers["location"].startswith("https://"):
                    # Absolute redirect
                    new_url_info = URL(response_headers["location"]).url_info
                    if not isinstance(new_url_info, HttpUrlInfo):
                        raise ValueError(
                            f"Redirect URL must be HTTP/HTTPS, got {type(new_url_info)}"
                        )
                    url_info = new_url_info
                else:
                    # Relative redirect - construct absolute URL from current URL
                    relative_path = response_headers["location"]

                    # Build absolute URL from current url_info and relative path
                    absolute_url = f"{url_info.scheme}://{url_info.host}"

                    # Add port if non-default
                    default_port = 443 if url_info.scheme == "https" else 80
                    if url_info.port != default_port:
                        absolute_url += f":{url_info.port}"

                    # Handle different types of relative paths
                    if relative_path.startswith("/"):
                        # Absolute path (relative to host)
                        absolute_url += relative_path
                    else:
                        # Relative path - resolve relative to current path
                        current_path = url_info.path or "/"
                        # Get directory of current path
                        if "/" in current_path:
                            current_dir = current_path.rsplit("/", 1)[0]
                        else:
                            current_dir = ""
                        absolute_url += f"{current_dir}/{relative_path}"

                    new_url_info = URL(absolute_url).url_info
                    if not isinstance(new_url_info, HttpUrlInfo):
                        raise ValueError(
                            f"Redirect URL must be HTTP/HTTPS, got {type(new_url_info)}"
                        )
                    url_info = new_url_info

                redirect_count -= 1
                self.socket.close()
                self.socket = None
                continue

            break

        content = ""
        if "content-length" in response_headers:
            content_length = int(response_headers["content-length"])
            content = response.read(content_length).decode("utf-8")
        elif (
            "transfer-encoding" in response_headers
            and response_headers["transfer-encoding"].lower() == "chunked"
        ):
            chunked_data = self.__read_chunked_body(response)
            # Handle gzip encoding if present
            if (
                "content-encoding" in response_headers
                and response_headers["content-encoding"].lower() == "gzip"
            ):
                import gzip

                decompressed_data = gzip.decompress(chunked_data)
                content = decompressed_data.decode("utf-8")
            else:
                content = chunked_data.decode("utf-8")
        else:
            content = response.read().decode("utf-8")

        if "cache-control" in response_headers:
            cache_control = response_headers["cache-control"]

            directives = [d.strip() for d in cache_control.split(",")]
            if "no-store" in directives:
                self.browser_cache.delete(BrowserCacheKey.from_http_info(url_info))
            else:
                for directive in directives:
                    if not directive.startswith("max-age="):
                        continue

                    max_age = int(directive[len("max-age=") :])
                    cached_content = self.browser_cache.get(
                        BrowserCacheKey.from_http_info(url_info)
                    )
                    if cached_content:
                        age = (
                            (datetime.now() - cached_content.timestamp).total_seconds()
                            if cached_content.timestamp
                            else 0
                        )
                        if age < cached_content.max_age:
                            content = cached_content.content
                        else:
                            self.browser_cache.set(
                                BrowserCacheKey.from_http_info(url_info),
                                BrowserCacheEntry(
                                    content=content,
                                    max_age=max_age,
                                    timestamp=datetime.now(),
                                ),
                            )
                    else:
                        self.browser_cache.set(
                            BrowserCacheKey.from_http_info(url_info),
                            BrowserCacheEntry(
                                content=content,
                                max_age=max_age,
                                timestamp=datetime.now(),
                            ),
                        )

        return content

    def request(self, url: URL) -> str:
        if isinstance(url.url_info, DataUrlInfo):
            return self.__request_data(url.url_info)
        elif isinstance(url.url_info, FileUrlInfo):
            return self.__request_file(url.url_info)
        elif isinstance(url.url_info, AboutUrlInfo):
            return self.__request_about(url.url_info)
        else:
            return self.__request_http(url.url_info, http_options=self.http_options)
