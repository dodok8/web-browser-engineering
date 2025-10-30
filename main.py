from soyorin.browser import Browser
import tkinter
from soyorin.url import URL
import sys
import os
from pathlib import Path


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


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Check if second argument is provided and is "True" (case-insensitive)
        use_memory_cache = len(sys.argv) > 2 and sys.argv[2].lower() == "true"
        Browser().load(URL(sys.argv[1]), use_memory_cache=use_memory_cache)
    else:
        # Load blank.html from the same directory when no argument is provided
        blank_path = Path(__file__).parent / "blank.html"
        Browser().load(URL(blank_path.as_uri()))
    tkinter.mainloop()
