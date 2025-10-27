from soyorin.cache import FileCache, InMemoryCache
from soyorin.url import URL
from soyorin.connection import Connection
import sys
import os


def show(body, view_source: bool):
    if view_source:
        print(body, end="")
    else:
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


def load(url: URL, use_memory_cache: bool = False):
    if use_memory_cache:
        cache = InMemoryCache()
    else:
        cache = FileCache(cache_dir="cache")

    connection = Connection(http_options={"http_version": "1.1"}, cache=cache)
    body = connection.request(url=url)
    show(body, view_source=url.view_source)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Check if second argument is provided and is "True" (case-insensitive)
        use_memory_cache = len(sys.argv) > 2 and sys.argv[2].lower() == "true"
        load(URL(sys.argv[1]), use_memory_cache=use_memory_cache)
    else:
        # Load blank.html from the same directory when no argument is provided
        blank_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "blank.html"
        )
        load(URL(f"file://{blank_path}"))
