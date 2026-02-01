from typing import Optional
from argparse import MetavarTypeHelpFormatter
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
        self.tabs = []
        self.active_tab: Optional[Tab] = None
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, width=WIDTH, height=HEIGHT, bg="white"
        )
        self.canvas.pack(fill=tkinter.BOTH, expand=True)
        self.display_list = []

        self.window.bind("<Down>", self.handle_down)
        self.window.bind("<Up>", self.handle_up)
        self.window.bind("<MouseWheel>", self.handle_scroll)
        self.window.bind("<Button-4>", self.handle_scroll)
        self.window.bind("<Button-5>", self.handle_scroll)
        self.window.bind("<Button-1>", self.handle_click)

        self.width = 800
        self.height = 600

    def draw(self):
        self.canvas.delete("all")
        if self.active_tab:
            self.active_tab.draw(self.canvas)

    def handle_down(self, e):
        if self.active_tab:
            self.active_tab.scroll_down()
            self.draw()

    def handle_up(self, e):
        if self.active_tab:
            self.active_tab.scroll_up()
            self.draw()

    def handle_scroll(self, e: tkinter.Event):
        if self.active_tab:
            self.active_tab.scroll_wheel(e)
            self.draw()

    def handle_click(self, e: tkinter.Event):
        if self.active_tab:
            self.active_tab.click(e.x, e.y)

    def new_tab(self, url, use_memory_cache: bool = False):
        new_tab = Tab()
        new_tab.load(url, use_memory_cache)
        self.active_tab = new_tab
        self.tabs.append(new_tab)
        self.draw()


class Tab:
    def __init__(self):
        self.scroll = 0.0

    def click(self, x, y):
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

    def scroll_wheel(self, e: tkinter.Event):
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

    def scroll_down(self):
        max_y = max(self.document.height + 2 * VSTEP - HEIGHT, 0)
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)

    def scroll_up(self):
        self.scroll = max(self.scroll - SCROLL_STEP, 0)

    def draw(self, canvas):
        canvas.delete("all")
        for cmd in self.display_list:
            if cmd.top > self.scroll + HEIGHT:
                continue
            if cmd.bottom < self.scroll:
                continue
            cmd.execute(self.scroll, canvas)

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
