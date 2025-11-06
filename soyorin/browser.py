from tkinter.font import Font
from tkinter import PhotoImage
from soyorin.lexer import Text
from soyorin.lexer import Tag
from soyorin.layout import Layout
from soyorin.connection import Connection
from soyorin.cache import FileCache, InMemoryCache
from soyorin.url import URL
from soyorin.lexer import Lexer
import tkinter
import platform


class Browser:
    SCROLL_BAR_WIDTH = 10
    SCROLL_STEP = 18

    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=800, height=600)
        self.lexer = Lexer()
        self.canvas.pack(fill=tkinter.BOTH, expand=True)
        self.layout = Layout(800 - Browser.SCROLL_BAR_WIDTH, 600, hstep=13, vstep=18)
        self.display_list: list[
            tuple[float, float, PhotoImage] | tuple[float, float, str, Font]
        ] = []

        self.text: list[Tag | Text] = []

        self.scroll = 0.0
        self.window.bind("<Down>", self.__scroll_down)
        self.window.bind("<Up>", self.__scroll_up)
        self.window.bind("<MouseWheel>", self.__scroll_wheel)
        self.window.bind("<Button-4>", self.__scroll_wheel)
        self.window.bind("<Button-5>", self.__scroll_wheel)

        self.window.bind("<Configure>", self.__resize)

    def __resize(self, e: tkinter.Event):
        self.layout.height = e.height
        self.layout.width = e.width
        self.display_list = self.layout.layout(self.text)
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

        max_scroll = max(0.0, self.layout.content_height - self.layout.height)
        if self.scroll > max_scroll:
            self.scroll = max_scroll

        self.draw()

    def __scroll_down(self, e):
        self.scroll += Browser.SCROLL_STEP
        max_scroll = max(0.0, self.layout.content_height - self.layout.height)
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
        for item in self.display_list:
            x = item[0]
            y = item[1]
            if y > self.scroll + self.layout.height:
                continue
            if y + self.layout.vstep < self.scroll:
                continue
            if len(item) == 4:  # Text with font: (x, y, text, font)
                self.canvas.create_text(
                    x, y - self.scroll, text=item[2], anchor="nw", font=item[3]
                )
            else:  # Emoji/Image: (x, y, image)
                self.canvas.create_image(x, y - self.scroll, image=item[2], anchor="nw")
        if ((self.scroll + self.layout.height) / self.layout.content_height) <= 1:
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
        self.display_list = self.layout.layout(self.text)
        self.draw()
