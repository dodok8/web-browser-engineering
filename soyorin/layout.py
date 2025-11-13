from tkinter import Label
from typing import Optional
from soyorin.lexer import Tag
from soyorin.lexer import Text
from soyorin.emoji import EmojiCache
import tkinter
from tkinter.font import Font
from tkinter import PhotoImage
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
        tokens: list[Tag | Text],
    ):
        self.width = width
        self.height = height
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.content_height = HSTEP
        self.emoji_cache = EmojiCache()

        self.display_list: list[
            tuple[float, float, PhotoImage] | tuple[float, float, str, Font]
        ] = []

        self.weight: Literal["normal", "bold"] = "normal"
        self.style: Literal["roman", "italic"] = "roman"
        self.size = 12
        self.line: list[tuple[float, str, Font]] = []
        self.line_sup_depths: list[int] = []
        self.is_center = False
        self.sup_depth = 0
        self.is_pre = False

        for tok in tokens:
            self.token(tok)
        self.flush()

    def split_text_and_emojis(self, text: str):

        emoji_patterns = [
            r"(?:[\p{Extended_Pictographic}][\U0001F3FB-\U0001F3FF]?[\uFE0E\uFE0F]?)(?:\u200d(?:[\p{Extended_Pictographic}][\U0001F3FB-\U0001F3FF]?[\uFE0E\uFE0F]?))+",
            r"[\U0001F1E6-\U0001F1FF]{2}",
            r"[\p{Extended_Pictographic}][\U0001F3FB-\U0001F3FF][\uFE0E\uFE0F]?",
            r"[\p{Extended_Pictographic}][\uFE0E\uFE0F]?",
        ]

        # 텍스트 패턴들 (인덱스 4-5)
        text_patterns = [
            r"\w+",
            r"\s+",
            r"\S",
        ]

        # 모든 패턴을 그룹으로 만들기
        all_patterns = []
        for pattern in emoji_patterns:
            all_patterns.append(f"({pattern})")
        for pattern in text_patterns:
            all_patterns.append(f"({pattern})")
        combined_pattern = "|".join(all_patterns)

        matches = regex.finditer(combined_pattern, text)

        result: list[Tuple[bool, str]] = []
        for match in matches:
            for i, group in enumerate(match.groups(), 1):
                if group is not None:
                    token: str = group
                    is_emoji = i <= len(emoji_patterns)

                    result.append((is_emoji, token))

        return result

    def token(self, tok: Text | Tag):

        if isinstance(tok, Text):
            if self.is_pre:
                print([word for _, word in self.split_text_and_emojis(tok.text)])
            for is_emoji, word in self.split_text_and_emojis(tok.text):
                self.word(is_emoji, word)
            self.content_height = self.cursor_y
        elif tok.tag == "i":
            self.style = "italic"
        elif tok.tag == "/i":
            self.style = "roman"
        elif tok.tag == "b":
            self.weight = "bold"
        elif tok.tag == "/b":
            self.weight = "normal"
        elif tok.tag == "small":
            self.size -= 2
        elif tok.tag == "/small":
            self.size += 2
        elif tok.tag == "big":
            self.size += 4
        elif tok.tag == "/big":
            self.size -= 4
        elif tok.tag == "br":
            self.flush()
        elif tok.tag == "br /":
            self.flush()
        elif tok.tag == "/p":
            self.flush()
            # self.cursor_y += VSTEP
        elif tok.tag == "center":
            self.flush()
            self.is_center = True
        elif tok.tag == "/center":
            self.flush()
            self.is_center = False
        elif tok.tag == "sup":
            self.sup_depth += 1
        elif tok.tag == "/sup":
            self.sup_depth -= 1
        elif tok.tag == "pre":
            self.flush()
            self.is_pre = True
        elif tok.tag == "/pre":
            self.is_pre = False

    def word(self, is_emoji: bool, word: str):
        if regex.match(r"\s+", word) and not self.is_pre:
            return
        font = get_font(self.size / (2**self.sup_depth), self.weight, self.style)

        if is_emoji:
            w = font.measure(word[0])
            emoji_code = "-".join([format(ord(letter), "X") for letter in word])
            emoji_picture = self.emoji_cache.get(emoji_code)
            if emoji_picture:
                self.display_list.append((self.cursor_x, self.cursor_y, emoji_picture))
        elif self.is_pre:
            font = get_font(
                self.size / (2**self.sup_depth), self.weight, self.style, "Courier New"
            )
            w = font.measure(word)
            self.line.append((self.cursor_x, word, font))
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
                x += font.measure(word + " ")
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
