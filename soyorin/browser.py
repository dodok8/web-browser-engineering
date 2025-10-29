from soyorin.layout import Layout
from soyorin.connection import Connection
from soyorin.cache import FileCache, InMemoryCache
from soyorin.url import URL
from soyorin.lexer import Lexer

import tkinter
import platform


class Browser:
    WIDTH, HEIGHT = 800, 600
    SCROLL_STEP = 18

    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, width=Browser.WIDTH, height=Browser.HEIGHT
        )
        self.lexer = Lexer()
        self.canvas.pack()
        self.layout = Layout(Browser.WIDTH, Browser.HEIGHT, hstep=13, vstep=18)

        self.scroll = 0.0
        self.window.bind("<Down>", self.__scroll_down)
        self.window.bind("<Up>", self.__scroll_up)
        self.window.bind("<MouseWheel>", self.__scroll_wheel)
        self.window.bind("<Button-4>", self.__scroll_wheel)
        self.window.bind("<Button-5>", self.__scroll_wheel)

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

        self.draw()

    def __scroll_down(self, e):
        self.scroll += Browser.SCROLL_STEP
        self.draw()

    def __scroll_up(self, e):
        self.scroll -= Browser.SCROLL_STEP
        if self.scroll < 0:
            self.scroll = 0
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.layout.display_list:
            if y > self.scroll + Browser.HEIGHT:
                continue
            if y + self.layout.vstep < self.scroll:
                continue
            self.canvas.create_text(x, y - self.scroll, text=c)

    def load(self, url: URL, use_memory_cache: bool = False):
        if use_memory_cache:
            cache = InMemoryCache()
        else:
            cache = FileCache(cache_dir="cache")

        connection = Connection(http_options={"http_version": "1.1"}, cache=cache)
        body = connection.request(url=url)
        text = self.lexer.lex(body, view_source=url.view_source)
        self.layout.update_layout(text)
        self.draw()
