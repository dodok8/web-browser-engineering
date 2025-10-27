from soyorin.connection import Connection
from soyorin.cache import FileCache, InMemoryCache
from soyorin.url import URL
from soyorin.lexer import Lexer
import tkinter
import tkinter.font


class Browser:
    WIDTH, HEIGHT = 800, 600

    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, width=Browser.WIDTH, height=Browser.HEIGHT
        )
        self.lexer = Lexer()
        self.canvas.pack()
        self.font = tkinter.font.Font(family="Noto Serif KR", size=12)

    def load(self, url: URL, use_memory_cache: bool = False):
        self.canvas
        if use_memory_cache:
            cache = InMemoryCache()
        else:
            cache = FileCache(cache_dir="cache")

        connection = Connection(http_options={"http_version": "1.1"}, cache=cache)
        body = connection.request(url=url)
        text = self.lexer.lex(body, view_source=url.view_source)
        print(text)
        HSTEP, VSTEP = 100, 18
        cursor_x, cursor_y = HSTEP, VSTEP

        self.canvas.create_text(20, 20, text="Hi")
        for c in text:
            self.canvas.create_text(
                cursor_x, cursor_y, text=c, font=self.font, anchor="nw"
            )
            cursor_x += HSTEP
            if cursor_x >= Browser.WIDTH - HSTEP:
                cursor_y += HSTEP
                cursor_x = HSTEP
