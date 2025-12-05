from soyorin.layout import VSTEP
from soyorin.lexer import Token
from soyorin.layout import Layout
from soyorin.connection import Connection
from soyorin.cache import FileCache, InMemoryCache
from soyorin.url import URL
from soyorin.lexer import HTMLParser, print_tree
import tkinter
import platform


class Browser:
    SCROLL_BAR_WIDTH = 10
    SCROLL_STEP = 18

    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=800, height=600)
        self.canvas.pack(fill=tkinter.BOTH, expand=True)

        self.tokens: list[Token] = []

        self.scroll = 0.0
        self.window.bind("<Down>", self.__scroll_down)
        self.window.bind("<Up>", self.__scroll_up)
        self.window.bind("<MouseWheel>", self.__scroll_wheel)
        self.window.bind("<Button-4>", self.__scroll_wheel)
        self.window.bind("<Button-5>", self.__scroll_wheel)

        self.window.bind("<Configure>", self.__resize)

        self.width = 800
        self.height = 600

    def __resize(self, e: tkinter.Event):
        self.height = e.height
        self.width = e.width
        self.layout = Layout(
            self.width - Browser.SCROLL_BAR_WIDTH, self.height, node=self.nodes
        )
        self.display_list = self.layout.display_list
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
            if y + VSTEP < self.scroll:
                continue
            self.canvas.create_text(
                x, y - self.scroll, text=item[2], anchor="nw", font=item[3]
            )

    def load(self, url: URL, use_memory_cache: bool = False):
        if use_memory_cache:
            cache = InMemoryCache()
        else:
            cache = FileCache(cache_dir="cache")

        connection = Connection(http_options={"http_version": "1.1"}, cache=cache)
        body = connection.request(url=url)
        self.nodes = HTMLParser(body).parse()
        print_tree(self.nodes)

        self.layout = Layout(self.width, self.height, self.nodes)
        self.display_list = self.layout.display_list
        self.draw()
