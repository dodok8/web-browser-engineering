from pathlib import Path
from soyorin.draw import DrawRect
from soyorin.draw import DrawCommand
from soyorin.draw import DrawLine
from soyorin.draw import Rect
from soyorin.draw import DrawText
from soyorin.draw import DrawOutline
from soyorin.layout import get_font
from typing import Optional
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

        self.chrome = Chrome(self)

    def draw(self):
        self.canvas.delete("all")
        if self.active_tab:
            self.active_tab.draw(self.canvas, self.chrome.bottom)
        for cmd in self.chrome.paint():
            cmd.execute(0, self.canvas)

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

    def handle_click(self, e):
        if e.y < self.chrome.bottom:
            self.chrome.click(e.x, e.y)
        else:
            tab_y = e.y - self.chrome.bottom
            self.active_tab.click(e.x, tab_y)
        self.draw()

    def new_tab(self, url, use_memory_cache: bool = False):
        new_tab = Tab(HEIGHT - self.chrome.bottom)
        new_tab.load(url, use_memory_cache)
        self.active_tab = new_tab
        self.tabs.append(new_tab)
        self.draw()


class Tab:
    def __init__(self, tab_height):
        self.scroll = 0.0
        self.tab_height = tab_height

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

        max_y = max(self.document.height + 2 * VSTEP - self.tab_height, 0)
        self.scroll = min(max(self.scroll - delta, 0), max_y)

    def scroll_down(self):
        max_y = max(self.document.height + 2 * VSTEP - self.tab_height, 0)
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)

    def scroll_up(self):
        self.scroll = max(self.scroll - SCROLL_STEP, 0)

    def draw(self, canvas, offset):
        for cmd in self.display_list:
            if cmd.rect.top > self.scroll + self.tab_height:
                continue
            if cmd.rect.bottom < self.scroll:
                continue
            cmd.execute(self.scroll - offset, canvas)

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


class Chrome:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.font = get_font(20, "normal", "roman")
        self.font_height = self.font.metrics("linespace")

        self.padding = 5
        self.tabbar_top = 0
        self.tabbar_bottom = self.font_height + 2 * self.padding

        plus_width = self.font.measure("+") + 2 * self.padding
        self.newtab_rect = Rect(
            self.padding,
            self.padding,
            self.padding + plus_width,
            self.padding + self.font_height,
        )

        self.bottom = self.tabbar_bottom

    def tab_rect(self, i):
        tabs_start = self.newtab_rect.right + self.padding
        tab_width = self.font.measure("Tab X") + 2 * self.padding

        return Rect(
            tabs_start + tab_width * i,
            self.tabbar_top,
            tabs_start + tab_width * (i + 1),
            self.tabbar_bottom,
        )

    def paint(self):
        cmds: list[DrawCommand] = []

        cmds.append(DrawRect(Rect(0, 0, WIDTH, self.bottom), "white"))
        cmds.append(DrawLine(0, self.bottom, WIDTH, self.bottom, "black", 1))

        cmds.append(DrawOutline(self.newtab_rect, "black", 1))
        cmds.append(
            DrawText(
                self.newtab_rect.left + self.padding,
                self.newtab_rect.top,
                "+",
                self.font,
                "black",
            )
        )

        for i, tab in enumerate(self.browser.tabs):
            bounds = self.tab_rect(i)
            cmds.append(
                DrawLine(bounds.left, 0, bounds.left, bounds.bottom, "black", 1)
            )
            cmds.append(
                DrawLine(bounds.right, 0, bounds.right, bounds.bottom, "black", 2)
            )
            cmds.append(
                DrawText(
                    bounds.left + self.padding,
                    bounds.top + self.padding,
                    f"Tab {i}",
                    self.font,
                    "black",
                )
            )
            if tab == self.browser.active_tab:
                cmds.append(
                    DrawLine(0, bounds.bottom, bounds.left, bounds.bottom, "black", 1)
                )
                cmds.append(
                    DrawLine(
                        bounds.right, bounds.bottom, WIDTH, bounds.bottom, "black", 1
                    )
                )

        return cmds

    def click(self, x, y):
        self.focus = None
        if self.newtab_rect.contains_point(x, y):
            path = Path(__file__).parent.parent / "blank.html"
            url = URL(path.as_uri())
            self.browser.new_tab(url)
        else:
            for i, tab in enumerate(self.browser.tabs):
                if self.tab_rect(i).contains_point(x, y):
                    self.browser.active_tab = tab
                    break
