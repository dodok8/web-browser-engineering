import socket
import ssl


class URL:
    def __init__(self, url):
        try:
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
        except ValueError:
            self.scheme, url = url.split(":", 1)
            self.mediatype, url = url.split(",", 1)
            self.mediatype = self.mediatype.split(";")
            self.data = url

    def request(self, headers=dict()):
        if self.scheme == "data":
            return self.data
        elif self.scheme in ["https", "http"]:
            s = socket.socket(
                family=socket.AF_INET,
                type=socket.SOCK_STREAM,
            )
            s.connect((self.host, self.port))

            if self.scheme == "https":
                ctx = ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=self.host)

            request = "GET {} HTTP/1.1\r\n".format(self.path)
            request += "Host: {}\r\n".format(self.host)
            request += "Connection: close\r\n"
            for key in headers:
                request += "{}: {}\r\n".format(key, headers[key])
            request += "\r\n"
            s.send(request.encode("utf8"))

            response = s.makefile("r", encoding="utf8", newline="" "\r\n")

            statusline = response.readline()
            version, status, explanation = statusline.split(" ", 2)

            response_headers = {}
            while True:
                line = response.readline()
                if line == "\r\n":
                    break
                header, value = line.split(":", 1)
                response_headers[header.casefold()] = value.strip()
            assert "transfer-encoding" not in response_headers
            assert "content-encoding" not in response_headers

            body = response.read()
            s.close()
        else:
            with open(self.path, "r") as file:
                body = file.read()

        return body


def show(body):
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")


def load(url):
    body = url.request({"User-Agent": "My-browser"})
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
