from __future__ import annotations
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
        self.children: list[BlockLayout | LineLayout] = []

        self.cursor_x = 0.0

        self.width = 0.0
        self.height = 0.0

        self.x = 0.0
        self.y = 0.0

    def recurse(self, node: Token):
        if isinstance(node, Text):
            for word in node.text.split():
                self.word(node, word)
        else:
            if node.tag == "br":
                self.new_line()
            for child in node.children:
                self.recurse(child)

    def word(self, node: Text, word: str):
        # Get font to calculate width for line breaking
        weight = node.style["font-weight"]
        style = node.style["font-style"]
        if style == "normal":
            style = "roman"
        size = int(float(node.style["font-size"][:-2]) * 0.75)
        assert weight in ("normal", "bold")
        assert style in ("roman", "italic")
        font = get_font(size, weight, style)
        w = font.measure(word)

        # Check if we need a new line
        if self.cursor_x + w > self.width:
            self.new_line()

        # Add word to current line
        line = self.children[-1]
        previous_word = line.children[-1] if line.children else None
        text = TextLayout(node, word, line, previous_word)
        line.children.append(text)

        self.cursor_x += w + font.measure(" ")

    def new_line(self):
        self.cursor_x = 0
        last_line = self.children[-1] if self.children else None
        new_line = LineLayout(self.node, self, last_line)
        self.children.append(new_line)


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
            self.new_line()
            self.recurse(self.node)

        for child in self.children:
            child.layout()

        self.height = sum([child.height for child in self.children])

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
            bullet_y = self.y + VSTEP / 2

            bullet_rect = DrawRect(
                bullet_x,
                bullet_y,
                bullet_x + bullet_size,
                bullet_y + bullet_size,
                "black",
            )
            cmds.append(bullet_rect)

        return cmds


class LineLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children: list[TextLayout] = []

    def layout(self):
        self.width = self.parent.width
        self.x = self.parent.x

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        if not self.children:
            self.height = 0
            return

        for word in self.children:
            word.layout()
        max_ascent = max([word.font.metrics("ascent") for word in self.children])
        baseline = self.y + 1.25 * max_ascent
        for word in self.children:
            word.y = baseline - word.font.metrics("ascent")
        max_descent = max([word.font.metrics("descent") for word in self.children])
        self.height = 1.25 * (max_ascent + max_descent)

    def paint(self):
        return []


class TextLayout:
    def __init__(self, node, word, parent, previous):
        self.node = node
        self.word = word
        self.children = []
        self.parent = parent
        self.previous = previous
        self.x = 0.0
        self.y = 0.0
        self.width = 0.0
        self.height = 0.0
        self.font = None

    def layout(self):
        weight = self.node.style["font-weight"]
        style = self.node.style["font-style"]
        if style == "normal":
            style = "roman"
        size = int(float(self.node.style["font-size"][:-2]) * 0.75)
        assert weight in ("normal", "bold")
        assert style in ("roman", "italic")
        self.font = get_font(size, weight, style)

        self.width = self.font.measure(self.word)

        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x

        self.height = self.font.metrics("linespace")

    def paint(self):
        color = self.node.style["color"]
        return [DrawText(self.x, self.y, self.word, self.font, color)]
