from soyorin.const import VSTEP
from soyorin.layout import paint_tree
from soyorin.const import SCROLL_STEP
from soyorin.const import HEIGHT
from soyorin.const import WIDTH
from soyorin.layout import DocumentLayout
from soyorin.connection import Connection
from soyorin.cache import FileCache, InMemoryCache
from soyorin.url import URL
from soyorin.lexer import HTMLParser, ViewSourceHTMLParser
import tkinter
import platform


class Browser:

    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack(fill=tkinter.BOTH, expand=True)
        self.display_list = []

        self.scroll = 0.0
        self.window.bind("<Down>", self.__scroll_down)
        self.window.bind("<Up>", self.__scroll_up)
        self.window.bind("<MouseWheel>", self.__scroll_wheel)
        self.window.bind("<Button-4>", self.__scroll_wheel)
        self.window.bind("<Button-5>", self.__scroll_wheel)

        self.width = 800
        self.height = 600

    def __scroll_wheel(self, e: tkinter.Event):
        if platform.system() == "Windows":
            delta = SCROLL_STEP * (e.delta / 120)
        elif platform.system() == "Darwin":
            delta = SCROLL_STEP * e.delta
        elif platform.system() == "Linux":
            if e.num == 4:  # Scroll up
                delta = SCROLL_STEP
            elif e.num == 5:  # Scroll down
                delta = -SCROLL_STEP
            else:
                delta = 0
        else:
            delta = 0

        max_y = max(self.document.height + 2 * VSTEP - HEIGHT, 0)
        self.scroll = min(max(self.scroll - delta, 0), max_y)
        self.draw()

    def __scroll_down(self, e):
        max_y = max(self.document.height + 2 * VSTEP - HEIGHT, 0)
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)
        self.draw()

    def __scroll_up(self, e):
        self.scroll = max(self.scroll - SCROLL_STEP, 0)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for cmd in self.display_list:
            if cmd.top > self.scroll + HEIGHT:
                continue
            if cmd.bottom < self.scroll:
                continue
            cmd.execute(self.scroll, self.canvas)

    def load(self, url: URL, use_memory_cache: bool = False):
        if use_memory_cache:
            cache = InMemoryCache()
        else:
            cache = FileCache(cache_dir="cache")

        connection = Connection(http_options={"http_version": "1.1"}, cache=cache)
        body = connection.request(url=url)

        if url.view_source:
            self.nodes = ViewSourceHTMLParser(body).parse()
        else:
            self.nodes = HTMLParser(body).parse()

        self.document = DocumentLayout(self.nodes)
        self.document.layout()
        paint_tree(self.document, self.display_list)
        self.draw()
