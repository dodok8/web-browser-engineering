import socket
import ssl


class URL:
    sockets = {}

    def __init__(self, url):
        self.view_source = False

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

    def request(self, headers=dict()):
        if self.scheme == "data":
            return self.data
        elif self.scheme in ["https", "http"]:
            cache_key = (self.scheme, self.host, self.port)

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
            for key in headers:
                request += "{}: {}\r\n".format(key, headers[key])
            request += "\r\n"
            s.send(request.encode("utf8"))

            response = s.makefile("rb", newline=b"\r\n")

            statusline = response.readline().decode("utf8")
            version, status, explanation = statusline.split(" ", 2)

            response_headers = {}
            while True:
                line = response.readline().decode("utf8")
                if line == "\r\n":
                    break
                header, value = line.split(":", 1)
                response_headers[header.casefold()] = value.strip()
                # 본문 길이가 주어져서 내려오므로, Transfer-Encoding은 필요 없다.
                # 단 view-source의 경우, chunked 로 내려오므로 이에 대한 처리가 필요하다.

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
        else:
            with open(self.path, "r") as file:
                body = file.read()

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
