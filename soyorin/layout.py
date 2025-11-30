from tkinter import Label
from typing import Optional
from soyorin.lexer import Text, Token
from soyorin.emoji import EmojiCache
import tkinter
from tkinter.font import Font
from typing import Tuple, Literal
import regex

HSTEP = 13.0
VSTEP = 18.0

FONTS: dict[
    Tuple[int, Literal["normal", "bold"], Literal["roman", "italic"], Optional[str]],
    Tuple[Font, Label],
] = {}


def get_font(
    size: int,
    weight: Literal["normal", "bold"],
    style: Literal["roman", "italic"],
    family="Times New Roman",
):
    size = int(size)  # Ensure size is always an integer
    key = (size, weight, style, family)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=style, family=family)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]


class Layout:

    def __init__(
        self,
        width: float,
        height: float,
        node: Token,
    ):
        self.width = width
        self.height = height
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.content_height = HSTEP
        self.emoji_cache = EmojiCache()

        self.display_list: list[tuple[float, float, str, Font]] = []

        self.weight: Literal["normal", "bold"] = "normal"
        self.style: Literal["roman", "italic"] = "roman"
        self.size = 12
        self.line: list[tuple[float, str, Font]] = []
        self.line_sup_depths: list[int] = []
        self.is_center = False
        self.sup_depth = 0
        self.is_pre = False

        self.recurse(node)
        self.flush()

    def open_tag(self, tag: str):
        if tag == "i":
            self.style = "italic"
        elif tag == "b":
            self.weight = "bold"
        elif tag == "small":
            self.size -= 2
        elif tag == "big":
            self.size += 4
        elif tag == "br":
            self.flush()
        elif tag == "center":
            self.flush()
            self.is_center = True
        elif tag == "sup":
            self.sup_depth += 1
        elif tag == "pre":
            self.flush()
            self.is_pre = True

    def close_tag(self, tag: str):
        if tag == "i":
            self.style = "roman"
        elif tag == "b":
            self.weight = "normal"
        elif tag == "small":
            self.size += 2
        elif tag == "big":
            self.size -= 4
        elif tag == "center":
            self.is_center = False
            self.flush()
        elif tag == "sup":
            self.sup_depth -= 1
        elif tag == "pre":
            self.is_pre = False
            self.flush()

    def recurse(self, tree: Token):
        if isinstance(tree, Text):
            for word in tree.text.split():
                self.word(word)
        else:
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree.tag)

    def word(self, word: str):
        if regex.match(r"\s+", word) and not self.is_pre:
            return
        font = get_font(self.size / (2**self.sup_depth), self.weight, self.style)

        if self.is_pre:
            if "\n" in word:
                for letter in word:
                    if letter == "\n":
                        if len(self.line) == 0:
                            self.cursor_y += VSTEP
                        else:
                            self.flush()
                return
            font = get_font(
                self.size / (2**self.sup_depth),
                self.weight,
                self.style,
                "Courier New",
            )
            w = font.measure(word)
            self.line.append(
                (
                    self.cursor_x,
                    word,
                    font,
                )
            )
            self.line_sup_depths.append(self.sup_depth)
        else:
            w = font.measure(word)
            self.line.append((self.cursor_x, word, font))
            self.line_sup_depths.append(self.sup_depth)
        self.cursor_x += w + font.measure(" ")
        if self.cursor_x + w >= self.width - HSTEP:
            self.flush()

    def flush(self):
        if not self.line:
            return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        tot_sup_offset = max(self.line_sup_depths)
        baseline = (
            self.cursor_y
            + (0.25 + sum([1 / 2**idx for idx in range(tot_sup_offset + 1)]))
            * max_ascent
        )
        if self.is_center:
            tot_x = sum([font.measure(word) for _, word, font in self.line])
            x = (self.width - tot_x) / 2.0
            for idx, (_, word, font) in enumerate(self.line):
                if self.line_sup_depths[idx] > 0:
                    y = baseline - max_ascent
                else:
                    y = baseline - font.metrics("ascent")
                self.display_list.append((x, y, word, font))
                x += font.measure(word)
        else:
            for idx, (x, word, font) in enumerate(self.line):
                if self.line_sup_depths[idx] > 0:
                    y = baseline - max_ascent
                else:
                    y = baseline - font.metrics("ascent")
                self.display_list.append((x, y, word, font))
                x += font.measure(word + " ")

        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

        self.cursor_x = HSTEP
        self.line = []
        self.line_sup_depths = []
