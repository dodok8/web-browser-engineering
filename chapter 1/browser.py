import os
import pickle
import socket
import ssl
import time
import hashlib
import gzip


class URL:
    sockets = {}
    cache = {}
    CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")

    def __init__(self, url):
        self.view_source = False
        self.MAX_REDIRECT = 30

        if url.startswith("data:"):
            self.scheme, url = url.split(":", 1)
            self.mediatype, url = url.split(",", 1)
            self.mediatype = self.mediatype.split(";")
            self.data = url
        else:
            if url.startswith("view-source:"):
                self.view_source = True
                _, url = url.split("view-source:", 1)
            self.scheme, url = url.split("://", 1)
            assert self.scheme in ["http", "https", "file"]

            if self.scheme == "file":
                self.host = ""
                self.path = url
                self.port = None
            else:
                if "/" not in url:
                    url = url + "/"
                self.host, url = url.split("/", 1)
                self.path = "/" + url

                if self.scheme == "http":
                    self.port = 80
                elif self.scheme == "https":
                    self.port = 443

                if ":" in self.host:
                    self.host, port = self.host.split(":", 1)
                    self.port = int(port)

    def __is_cached(self, cache_key):
        if cache_key in URL.cache:
            return True
        else:
            self.__load_cache_from_memory(cache_key)
            return cache_key in URL.cache

    def __load_cache_from_memory(self, cache_key):
        filename = self.__get_cache_filename(cache_key)
        if not os.path.exists(filename):
            pass
        try:
            with open(filename, "rb") as f:
                data = pickle.load(f)
                cache_entry = data["entry"]

                body, response_headers, status_code, cached_time, max_age = cache_entry
                if max_age is not None and (time.time() - cached_time) >= max_age:
                    os.remove(filename)  # cache 시간 확인후 필요없으면 삭제
                else:
                    URL.cache[cache_key] = cache_entry
        except FileNotFoundError:
            pass

    def __get_cache_filename(self, cache_key):
        hash = hashlib.sha256(str(cache_key).encode("utf-8")).hexdigest()
        return os.path.join(URL.CACHE_DIR, f"{hash}.cache")

    def __save_cache_to_disk(self, cache_key, cache_entry):
        filename = self.__get_cache_filename(cache_key)
        with open(filename, "wb") as f:
            pickle.dump({"entry": cache_entry}, f)

    def request(self, headers=dict(), redirect_count=0):
        if self.scheme == "data":
            return self.data
        elif self.scheme in ["https", "http"]:
            # Check redirect limit
            if redirect_count >= self.MAX_REDIRECT:
                raise Exception(
                    "Too many redirects (limit: {})".format(self.MAX_REDIRECT)
                )

            cache_key = (self.scheme, self.host, self.path, self.port)

            if cache_key in URL.sockets:
                s = URL.sockets[cache_key]
            else:
                s = socket.socket(
                    family=socket.AF_INET,
                    type=socket.SOCK_STREAM,
                )
                s.connect((self.host, self.port))

                if self.scheme == "https":
                    ctx = ssl.create_default_context()
                    s = ctx.wrap_socket(s, server_hostname=self.host)

                URL.sockets[cache_key] = s

            request = "GET {} HTTP/1.1\r\n".format(self.path)
            request += "Host: {}\r\n".format(self.host)
            request += "Connection: keep-alive\r\n"
            request += "Accept-Encoding: gzip"
            for key in headers:
                request += "{}: {}\r\n".format(key, headers[key])
            request += "\r\n"
            s.send(request.encode("utf8"))

            response = s.makefile("rb", newline=b"\r\n")

            status_line = response.readline().decode("utf8")
            version, status, explanation = status_line.split(" ", 2)

            response_headers = {}
            while True:
                line = response.readline().decode("utf8")
                if line == "\r\n":
                    break
                header, value = line.split(":", 1)
                response_headers[header.casefold()] = value.strip()

            # Handle cache
            if int(status) in [200] and self.__is_cached(cache_key):
                body, response_headers, status_code, cached_time, max_age = URL.cache[
                    cache_key
                ]
                return body
            # Handle redirects (300-399 status codes)
            elif 300 <= int(status) < 400:
                assert "location" in response_headers

                location = response_headers["location"]

                # Handle relative URLs (starting with /)
                if location.startswith("/"):
                    # Same scheme and host, new path
                    redirect_url = "{}://{}{}".format(self.scheme, self.host, location)
                    if self.port != (80 if self.scheme == "http" else 443):
                        redirect_url = "{}://{}:{}{}".format(
                            self.scheme, self.host, self.port, location
                        )
                else:
                    redirect_url = location

                # Follow the redirect
                new_url = URL(redirect_url)
                body = new_url.request(headers, redirect_count + 1)
            else:
                if (
                    "transfer-encoding" in response_headers
                    and response_headers["transfer-encoding"] == "chunked"
                ):
                    # chunked 파싱
                    body = ""
                    while True:
                        chunk_size_line = response.readline()
                        chunk_size_line = chunk_size_line.decode("utf-8").strip()
                        chunk_size = int(chunk_size_line, 16)  # hex to int
                        if chunk_size == 0:
                            break
                        chunk_data = response.read(chunk_size).decode("utf-8")
                        response.readline()  # \r\n 제거
                        body += chunk_data
                else:
                    content_length = int(response_headers["content-length"])
                    body = response.read(content_length).decode("utf-8")

                if (
                    "content-encoding" in response_headers
                    and response_headers["content-encoding"] == "gzip"
                ):
                    body = gzip.decompress(body)
        else:
            with open(self.path, "r") as file:
                body = file.read()

        should_cache = False
        max_age = None
        if int(status) in [404, 200]:
            if "cache-control" in response_headers:
                cache_control = response_headers["cache-control"]

                if "no-store" in cache_control:
                    pass
                elif "max-age=" in cache_control:
                    for directive in cache_control.split(","):
                        directive = directive.strip()
                        if directive.startswith("max-age="):
                            try:
                                max_age = int(directive.split("=")[1])
                                should_cache = True
                            except ValueError:
                                should_cache = False
                            break
        if should_cache:
            cache_entry = (body, response_headers, int(status), time.time(), max_age)
            URL.cache[cache_key] = cache_entry
            self.__save_cache_to_disk(cache_key, cache_entry)

        return body


def show(body):
    in_tag = False

    text = ""
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            text += c
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")

    print(text, end="")


def load(url):
    body = url.request({"User-Agent": "My-browser"})
    if url.view_source:
        print(body, end="")
    else:
        show(body)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        load(URL(" ".join(sys.argv[1:])))
    else:
        try:
            load(
                URL(
                    "file:///Users/dodok/repos/web-browser-engineering/"
                    "chapter 1/blank.html"
                )
            )
        except FileNotFoundError:
            load(
                URL(
                    "file:///home/dodok8/Development/web-browser-engineering/"
                    "chapter 1/blank.html"
                )
            )
