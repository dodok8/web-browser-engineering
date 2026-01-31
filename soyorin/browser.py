from soyorin.lexer import Text
import tkinter
from soyorin.style import cascade_priority
from soyorin.lexer import Element
from soyorin.tree import tree_to_list
from soyorin.style import CSSParser
from soyorin.style import style
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
import platform

DEFAULT_STYLE_SHEET = CSSParser(open("browser.css").read()).parse()


class Browser:

    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, width=WIDTH, height=HEIGHT, bg="white"
        )
        self.canvas.pack(fill=tkinter.BOTH, expand=True)
        self.display_list = []

        self.scroll = 0.0
        self.window.bind("<Down>", self.__scroll_down)
        self.window.bind("<Up>", self.__scroll_up)
        self.window.bind("<MouseWheel>", self.__scroll_wheel)
        self.window.bind("<Button-4>", self.__scroll_wheel)
        self.window.bind("<Button-5>", self.__scroll_wheel)
        self.window.bind("<Button-1>", self.click)

        self.width = 800
        self.height = 600

    def click(self, e):
        x, y = e.x, e.y
        y += self.scroll
        objs = [
            obj
            for obj in tree_to_list(self.document, [])
            if obj.x <= x < obj.x + obj.width and obj.y <= y < obj.y + obj.height
        ]
        if not objs:
            return
        elt = objs[-1].node
        while elt:
            if isinstance(elt, Text):
                pass
            elif elt.tag == "a" and "href" in elt.attributes:
                url = self.url.resolve(elt.attributes["href"])
                return self.load(url)
            elt = elt.parent

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
        self.url = url
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

        rules = DEFAULT_STYLE_SHEET.copy()

        links = [
            node.attributes["href"]
            for node in tree_to_list(self.nodes, [])
            if isinstance(node, Element)
            and node.tag == "link"
            and node.attributes.get("rel") == "stylesheet"
            and "href" in node.attributes
        ]

        for link in links:
            style_url = url.resolve(link)
            try:
                body = connection.request(url=style_url)
            except Exception:
                continue
            rules.extend(CSSParser(body).parse())

        style(self.nodes, sorted(rules, key=cascade_priority))
        self.document = DocumentLayout(self.nodes)
        self.document.layout()
        self.display_list = []
        paint_tree(self.document, self.display_list)
        self.draw()
