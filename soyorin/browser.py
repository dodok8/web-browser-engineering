from tkinter import PhotoImage
from typing import Optional
from typing import Dict
from pathlib import Path
import os
from soyorin.layout import Layout
from soyorin.connection import Connection
from soyorin.cache import FileCache, InMemoryCache
from soyorin.url import URL
from soyorin.lexer import Lexer

import tkinter
import platform


class Browser:
    WIDTH, HEIGHT = 800, 600
    SCROLL_BAR_WIDTH = 20
    SCROLL_STEP = 18

    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, width=Browser.WIDTH, height=Browser.HEIGHT
        )
        self.lexer = Lexer()
        self.canvas.pack(fill=tkinter.BOTH, expand=True)
        self.layout = Layout(
            Browser.WIDTH - Browser.SCROLL_BAR_WIDTH, Browser.HEIGHT, hstep=13, vstep=18
        )

        self.text = ""

        self.scroll = 0.0
        self.window.bind("<Down>", self.__scroll_down)
        self.window.bind("<Up>", self.__scroll_up)
        self.window.bind("<MouseWheel>", self.__scroll_wheel)
        self.window.bind("<Button-4>", self.__scroll_wheel)
        self.window.bind("<Button-5>", self.__scroll_wheel)

        self.window.bind("<Configure>", self.__resize)

        self.emoji_cache: Dict[str, Optional[PhotoImage]] = {}
        emoji_path = Path(__file__).parent.parent / "emoji"
        for emoji_file_name in os.listdir(emoji_path):
            emoji_code = emoji_file_name.strip(".png")
            self.emoji_cache[emoji_code] = None

    def __resize(self, e: tkinter.Event):
        self.layout.height = e.height
        self.layout.width = e.width
        self.layout.update_layout(self.text)
        self.draw()

    def __scroll_wheel(self, e: tkinter.Event):
        if platform.system() == "Windows":
            self.scroll -= Browser.SCROLL_STEP * (e.delta / 120)
        elif platform.system() == "Darwin":
            self.scroll -= Browser.SCROLL_STEP * e.delta
        elif platform.system() == "Linux":
            if e.num == 4:  # Scroll up
                self.scroll -= Browser.SCROLL_STEP
            elif e.num == 5:  # Scroll down
                self.scroll += Browser.SCROLL_STEP

        if self.scroll < 0:
            self.scroll = 0

        max_scroll = max(0, self.layout.content_height - self.layout.height)
        if self.scroll > max_scroll:
            self.scroll = max_scroll

        self.draw()

    def __scroll_down(self, e):
        self.scroll += Browser.SCROLL_STEP
        max_scroll = max(0, self.layout.content_height - self.layout.height)
        if self.scroll > max_scroll:
            self.scroll = max_scroll
        self.draw()

    def __scroll_up(self, e):
        self.scroll -= Browser.SCROLL_STEP
        if self.scroll < 0:
            self.scroll = 0
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.layout.display_list:
            if y > self.scroll + self.layout.height:
                continue
            if y + self.layout.vstep < self.scroll:
                continue
            emoji_code = format(ord(c), "X")  # Convert to uppercase hex
            if emoji_code in self.emoji_cache:
                if self.emoji_cache[emoji_code] is None:
                    self.emoji_cache[emoji_code] = tkinter.PhotoImage(
                        file=f"emoji/{emoji_code}.png"
                    )

                self.canvas.create_image(
                    x, y - self.scroll, image=self.emoji_cache[emoji_code]
                )
            else:
                self.canvas.create_text(x, y - self.scroll, text=c)

        if ((self.scroll + self.layout.height) / self.layout.content_height) < 1:
            # Draw Background of scroll bar
            self.canvas.create_rectangle(
                self.layout.width - self.SCROLL_BAR_WIDTH,
                0,
                self.layout.width,
                self.layout.height,
                fill="white",
                width=0,
            )

            # Draw scroll bar
            self.canvas.create_rectangle(
                self.layout.width - self.SCROLL_BAR_WIDTH,
                (self.scroll / self.layout.content_height) * self.layout.height,
                self.layout.width,
                ((self.scroll + self.layout.height) / self.layout.content_height)
                * self.layout.height,
                fill="blue",
                width=0,
            )

    def load(self, url: URL, use_memory_cache: bool = False):
        if use_memory_cache:
            cache = InMemoryCache()
        else:
            cache = FileCache(cache_dir="cache")

        connection = Connection(http_options={"http_version": "1.1"}, cache=cache)
        body = connection.request(url=url)
        self.text = self.lexer.lex(body, view_source=url.view_source)
        self.layout.update_layout(self.text)
        self.draw()
