from __future__ import annotations

from soyorin.font import get_font
from soyorin.const import VSTEP
from soyorin.const import HSTEP
from soyorin.draw import DrawRect
from soyorin.draw import DrawText
from soyorin.draw import Rect
from soyorin.const import WIDTH
from soyorin.lexer import Element

from soyorin.lexer import Text, Token
from tkinter.font import Font
from typing import cast


class DocumentLayout:
    def __init__(self, node: Token):
        self.node = node
        self.parent = None
        self.children: list[BlockLayout] = []
        self.width: float = WIDTH - 2 * HSTEP
        self.x: float = HSTEP
        self.y: float = VSTEP
        self.height: float = 0.0

    def layout(self) -> None:
        child = BlockLayout(self.node, self, None)
        self.children.append(child)
        child.layout()
        self.height = child.height

    def paint(self) -> list:
        return []


def paint_tree(
    layout_object: DocumentLayout | BlockLayout | LineLayout | TextLayout,
    display_list: list[DrawText | DrawRect],
) -> None:
    display_list.extend(layout_object.paint())

    for child in layout_object.children:
        paint_tree(child, display_list)


class BlockLayout:

    def __init__(
        self,
        node: Token,
        parent: DocumentLayout | BlockLayout,
        previous: BlockLayout | None,
    ):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children: list[BlockLayout | LineLayout] = []

        self.cursor_x: float = 0.0

        self.width: float = 0.0
        self.height: float = 0.0

        self.x: float = 0.0
        self.y: float = 0.0

    def recurse(self, node: Token) -> None:
        if isinstance(node, Text):
            for word in node.text.split():
                self.word(node, word)
        else:
            if node.tag == "br":
                self.new_line()
            for child in node.children:
                self.recurse(child)

    def word(self, node: Text, word: str) -> None:
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
        assert isinstance(line, LineLayout)
        previous_word = line.children[-1] if line.children else None
        text = TextLayout(node, word, line, previous_word)
        line.children.append(text)

        self.cursor_x += w + font.measure(" ")

    def new_line(self) -> None:
        self.cursor_x = 0
        last_line: LineLayout | None = None
        if self.children and isinstance(self.children[-1], LineLayout):
            last_line = cast(LineLayout, self.children[-1])
        line = LineLayout(self.node, self, last_line)
        self.children.append(line)

    def layout_mode(self) -> str:
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

    def layout(self) -> None:

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

    def paint(self) -> list[DrawText | DrawRect]:
        cmds: list[DrawText | DrawRect] = []

        bgcolor = self.node.style.get("background-color", "transparent")
        if bgcolor != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(Rect(self.x, self.y, x2, y2), bgcolor)
            cmds.append(rect)

        # Draw bullet for <li> elements
        if isinstance(self.node, Element) and self.node.tag == "li":
            bullet_size = 4
            bullet_x = self.x - HSTEP - bullet_size / 2
            bullet_y = self.y + VSTEP / 2

            bullet_rect = DrawRect(
                Rect(
                    bullet_x,
                    bullet_y,
                    bullet_x + bullet_size,
                    bullet_y + bullet_size,
                ),
                "black",
            )
            cmds.append(bullet_rect)

        return cmds


class LineLayout:
    def __init__(
        self, node: Token, parent: BlockLayout, previous: LineLayout | None
    ):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children: list[TextLayout] = []
        self.width: float = 0.0
        self.x: float = 0.0
        self.y: float = 0.0
        self.height: float = 0.0

    def layout(self) -> None:
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
        max_ascent = max(
            [
                word.font.metrics("ascent")
                for word in self.children
                if word.font is not None
            ]
        )
        baseline = self.y + 1.25 * max_ascent
        for word in self.children:
            if word.font is not None:
                word.y = baseline - word.font.metrics("ascent")
        max_descent = max(
            [
                word.font.metrics("descent")
                for word in self.children
                if word.font is not None
            ]
        )
        self.height = 1.25 * (max_ascent + max_descent)

    def paint(self) -> list:
        return []


class TextLayout:
    def __init__(
        self, node: Text, word: str, parent: LineLayout, previous: TextLayout | None
    ):
        self.node = node
        self.word = word
        self.children: list = []
        self.parent = parent
        self.previous = previous
        self.x: float = 0.0
        self.y: float = 0.0
        self.width: float = 0.0
        self.height: float = 0.0
        self.font: Font | None = None

    def layout(self) -> None:
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
            assert self.previous.font is not None
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x

        self.height = self.font.metrics("linespace")

    def paint(self) -> list[DrawText]:
        color = self.node.style["color"]
        assert self.font is not None
        return [DrawText(self.x, self.y, self.word, self.font, color)]
