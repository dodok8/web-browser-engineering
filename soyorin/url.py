from typing import Literal
from dataclasses import dataclass
import re

# moreal 님의 코드에서 가져온 걸 일부 변형
# https://github.com/moreal/web-browser-engineering-book/blob/main/browser/url.py


@dataclass(frozen=True)
class HttpUrlInfo:
    scheme: Literal["http", "https"]
    username: str | None
    password: str | None
    host: str | None
    port: int
    path: str | None
    query: str | None
    fragment: str | None


@dataclass(frozen=True)
class FileUrlInfo:
    host: str
    path: str | None


@dataclass(frozen=True)
class DataUrlInfo:
    mediatype: str
    parameters: dict[str, str]
    is_base64: bool
    data: str


@dataclass(frozen=True)
class AboutUrlInfo:
    path: Literal["blank"]


class URL:
    view_source: bool
    url_info: HttpUrlInfo | FileUrlInfo | DataUrlInfo | AboutUrlInfo

    def __init__(self, url: str):
        self.view_source = False
        if url.startswith("view-source:"):
            self.view_source = True
            url = url[12:]

        if url.startswith("about:"):
            scheme, path = url.split(":")
            if path == "blank":
                self.url_info = AboutUrlInfo(path=path)
            else:
                raise ValueError("Unsupported about: scheme")
            return
        if url.startswith("data"):
            if not url:
                # Minimal data URI: "data:,"
                url = ","

            # The comma is required and separates metadata from data
            if "," not in url:
                raise ValueError("Invalid data URI: missing comma separator")

            metadata, data = url.split(",", 1)

            # Parse metadata part: [<mediatype>][;<param>=<value>]*[;base64]
            parts = metadata.split(";") if metadata else []

            # First part is the mediatype (if present and not a parameter)
            mediatype = "text/plain"
            parameters: dict[str, str] = {}
            is_base64 = False

            for i, part in enumerate(parts):
                part = part.strip()
                if not part:
                    continue

                # Check if it's "base64" indicator
                if part.lower() == "base64":
                    is_base64 = True
                # Check if it's a parameter (contains '=')
                elif "=" in part:
                    key, value = part.split("=", 1)
                    parameters[key.strip()] = value.strip()
                # First non-parameter, non-base64 part is the mediatype
                elif i == 0:
                    mediatype = part
                else:
                    # If we encounter a part without '=' that's not first and not 'base64',
                    # it might be a malformed URI, but we'll treat it as part of mediatype
                    pass

            # Set default charset if not specified and mediatype is text/plain
            if mediatype == "text/plain" and "charset" not in parameters:
                parameters["charset"] = "US-ASCII"

            self.url_info = DataUrlInfo(
                mediatype=mediatype,
                parameters=parameters,
                is_base64=is_base64,
                data=data,
            )
            return
        self.url_info = self.__parse_url(url)

    def __parse_url(self, url: str) -> FileUrlInfo | HttpUrlInfo:

        # RFC 3986 compliant URL regex pattern
        # URI = scheme ":" ["//" authority] path ["?" query] ["#" fragment]
        # authority = [userinfo "@"] host [":" port]

        # Scheme: starts with letter, followed by letters, digits, +, -, or .
        scheme = r"(?P<scheme>[a-zA-Z][a-zA-Z0-9+.-]*)"

        # Userinfo (optional): username[:password]@
        # Unreserved: A-Z a-z 0-9 - . _ ~
        # Sub-delims: ! $ & ' ( ) * + , ; =
        # Also allows : and percent-encoded chars
        userinfo = r"(?:(?P<username>[a-zA-Z0-9\-._~!$&'()*+,;=%]+)(?::(?P<password>[a-zA-Z0-9\-._~!$&'()*+,;=%]*))?@)?"

        # Host can be:
        # - IPv6: enclosed in brackets [...]
        # - IPv4: dot-decimal notation
        # - Registered name: letters, digits, hyphens, dots, underscores, tildes
        ipv6 = r"\[[0-9a-fA-F:]+\]"
        ipv4 = r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}"
        registered_name = r"[a-zA-Z0-9\-._~!$&'()*+,;=%]*"
        host = rf"(?P<hostname>{ipv6}|{ipv4}|{registered_name})"

        # Port (optional): decimal digits
        port = r"(?::(?P<port>\d+))?"

        # Authority (optional): [userinfo "@"] host [":" port]
        authority = rf"(?://(?:{userinfo}{host}{port}))?"

        # Path: sequence of segments separated by /
        # Can contain unreserved chars, percent-encoded, sub-delims, :, @
        # For URIs without authority, path can contain additional characters
        # Matches everything except ? and # (which start query and fragment)
        path = r"(?P<path>[^?#]*)"

        # Query (optional): after ?, can contain any character except #
        query = r"(?:\?(?P<query>[^#]*))?"

        # Fragment (optional): after #, can contain any remaining characters
        fragment = r"(?:#(?P<fragment>.*))?"

        # Complete regex pattern
        regex = rf"^{scheme}:{authority}{path}{query}{fragment}$"

        match = re.match(regex, url)
        if not match:
            raise ValueError("Invalid URL")

        scheme_value = match.group("scheme")
        username_value = match.group("username")
        password_value = match.group("password")
        hostname_value = match.group("hostname") or None
        if match.group("port"):
            port_value = int(match.group("port"))
        elif scheme_value == "http":
            port_value = 80
        else:
            # https
            port_value = 443
        path_value = match.group("path") or None
        query_value = match.group("query")
        fragment_value = match.group("fragment")

        if scheme_value in ["http", "https"]:
            return HttpUrlInfo(
                scheme_value,
                username_value,
                password_value,
                hostname_value,
                port_value,
                path_value,
                query_value,
                fragment_value,
            )
        else:
            return FileUrlInfo(host=hostname_value or "localhost", path=path_value)

    def resolve(self, url: str) -> "URL":
        if "://" in url:
            return URL(url)
        if url.startswith("//"):
            if isinstance(self.url_info, HttpUrlInfo):
                return URL(self.url_info.scheme + ":" + url)
            raise ValueError("Cannot resolve scheme-relative URL for non-HTTP URL")
        if not isinstance(self.url_info, HttpUrlInfo):
            raise ValueError("Cannot resolve relative URL for non-HTTP URL")

        path = self.url_info.path or "/"
        if url.startswith("/"):
            new_path = url
        else:
            dir, _ = path.rsplit("/", 1)
            while url.startswith("../"):
                _, url = url.split("/", 1)
                if "/" in dir:
                    dir, _ = dir.rsplit("/", 1)
            new_path = dir + "/" + url

        new_url = f"{self.url_info.scheme}://"
        if self.url_info.username:
            new_url += self.url_info.username
            if self.url_info.password:
                new_url += ":" + self.url_info.password
            new_url += "@"
        new_url += self.url_info.host or ""
        if (self.url_info.scheme == "http" and self.url_info.port != 80) or \
           (self.url_info.scheme == "https" and self.url_info.port != 443):
            new_url += ":" + str(self.url_info.port)
        new_url += new_path
        return URL(new_url)
