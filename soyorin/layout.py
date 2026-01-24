from soyorin.const import VSTEP
from soyorin.const import HSTEP
from soyorin.commnad import DrawRect
from soyorin.commnad import DrawText
from soyorin.const import WIDTH
from soyorin.lexer import Element
from tkinter import Label
from typing import Optional
from soyorin.lexer import Text, Token
import tkinter
from tkinter.font import Font
from typing import Tuple, Literal

FONTS: dict[
    Tuple[int, Literal["normal", "bold"], Literal["roman", "italic"], Optional[str]],
    Tuple[Font, Label],
] = {}


def get_font(
    size: int,
    weight: Literal["normal", "bold"],
    style: Literal["roman", "italic"],
    family="D2Coding",
):
    size = int(size)  # Ensure size is always an integer
    key = (size, weight, style, family)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=style, family=family)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]


class DocumentLayout:
    def __init__(self, node: Token):
        self.node = node
        self.parent = None
        self.children = []
        self.width = WIDTH - 2 * HSTEP
        self.x = HSTEP
        self.y = VSTEP

    def layout(self):
        child = BlockLayout(self.node, self, None)
        self.children.append(child)
        child.layout()
        self.height = child.height

    def paint(self):
        return []


def paint_tree(layout_object, display_list):
    display_list.extend(layout_object.paint())

    for child in layout_object.children:
        paint_tree(child, display_list)


class BlockLayout:

    def __init__(
        self,
        node: Token,
        parent,
        previous,
    ):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children: list[BlockLayout] = []

        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.content_height = HSTEP

        self.width = 0.0
        self.height = 0.0

        self.x = 0.0
        self.y = 0.0
        self.display_list = []

        self.display_list: list[tuple[float, float, str, Font, str]] = []

        self.line: list[tuple[float, str, Font, str]] = []

    def recurse(self, node: Token):
        if isinstance(node, Text):
            for word in node.text.split():
                self.word(node, word)
        else:
            if node.tag == "br":
                self.flush()
            for child in node.children:
                self.recurse(child)

    def word(self, node: Text, word: str):
        color = node.style["color"]
        weight = node.style["font-weight"]
        style = node.style["font-style"]
        if style == "normal":
            style = "roman"
        size = int(float(node.style["font-size"][:-2]) * 0.75)
        assert weight in ("normal", "bold")
        assert style in ("roman", "italic")
        font = get_font(size, weight, style)
        w = font.measure(word)
        self.line.append((self.cursor_x, word, font, color))
        self.cursor_x += w + font.measure(" ")
        if self.cursor_x + w >= self.width:
            self.flush()

    def flush(self):
        if not self.line:
            return
        metrics = [font.metrics() for x, word, font, color in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        for rel_x, word, font, color in self.line:
            x = self.x + rel_x
            y = self.y + baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font, color))

        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

        self.cursor_x = 0
        self.line = []

    def layout_mode(self):
        if isinstance(self.node, Text):
            return "inline"
        elif any(
            [
                isinstance(child, Element)
                and child.style.get("display", "inline") == "block"
                for child in self.node.children
            ]
        ):
            return "block"
        elif self.node.children:
            return "inline"
        else:
            return "block"

    def layout(self):

        self.x = self.parent.x
        self.width = self.parent.width

        # Add indentation for <li> elements
        if isinstance(self.node, Element) and self.node.tag == "li":
            self.x += 2 * HSTEP
            self.width -= 2 * HSTEP

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        mode = self.layout_mode()
        if mode == "block":
            previous = None
            for child in self.node.children:
                next = BlockLayout(child, self, previous)
                if isinstance(child, Element) and child.tag == "head":
                    continue
                self.children.append(next)
                previous = next
        else:
            self.cursor_x = 0
            self.cursor_y = 0
            self.line = []
            self.recurse(self.node)
            self.flush()

        for child in self.children:
            child.layout()

        if mode == "block":
            self.height = sum([child.height for child in self.children])
        else:
            self.height = self.cursor_y

    def paint(self):
        cmds: list[DrawText | DrawRect] = []

        bgcolor = self.node.style.get("background-color", "transparent")
        if bgcolor != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, bgcolor)
            cmds.append(rect)

        # Draw bullet for <li> elements
        if isinstance(self.node, Element) and self.node.tag == "li":
            bullet_size = 4
            bullet_x = self.x - HSTEP - bullet_size / 2

            # Find the first display list (either in self or first child)
            if self.display_list:
                first_font = self.display_list[0][3]
                first_y = self.display_list[0][1]
                bullet_y = first_y + first_font.metrics("ascent") / 2 - bullet_size / 2
            elif self.children and self.children[0].display_list:
                first_font = self.children[0].display_list[0][3]
                first_y = self.children[0].display_list[0][1]
                bullet_y = first_y + first_font.metrics("ascent") / 2 - bullet_size / 2
            else:
                # Fallback if no text yet
                bullet_y = self.y + VSTEP / 2

            bullet_rect = DrawRect(
                bullet_x,
                bullet_y,
                bullet_x + bullet_size,
                bullet_y + bullet_size,
                "black",
            )
            cmds.append(bullet_rect)

        if self.layout_mode() == "inline":
            for x, y, word, font, color in self.display_list:
                cmds.append(DrawText(x, y, word, font, color))

        return cmds
