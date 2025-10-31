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

    browser = Browser()
    # 캐싱 등으로 소요되는 시간을 감안해서 미리 객체를 생성해 놓는 식으로 변경
    try:
        if len(sys.argv) > 1:
            # Check if second argument is provided and is "True" (case-insensitive)
            use_memory_cache = len(sys.argv) > 2 and sys.argv[2].lower() == "true"
            path = sys.argv[1]
            url = URL(path)
        else:
            # Load blank.html from the same directory when no argument is provided
            path = Path(__file__).parent / "blank.html"
            url = URL(path.as_uri())
        browser.load(url)
    except Exception:
        url = URL("about:blank")
        browser.load(url)
    tkinter.mainloop()
