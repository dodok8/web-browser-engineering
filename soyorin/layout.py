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

FONTS = {}


def get_font(size, weight, style):
    key = (size, weight, style)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=style)
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
        self.line = []

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
            # 어떤 그룹이 매치되었는지 확인
            for i, group in enumerate(match.groups(), 1):
                if group is not None:
                    token: str = group
                    # 그룹 인덱스가 1-4면 이모지, 5-6이면 텍스트
                    is_emoji = i <= len(emoji_patterns)

                    result.append((is_emoji, token))

        return result

    def token(self, tok: Text | Tag):

        if isinstance(tok, Text):
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
        elif tok.tag == "/p":
            self.flush()
            self.cursor_y += VSTEP

    def word(self, is_emoji: bool, word: str):
        font = get_font(self.size, self.weight, self.style)

        if is_emoji:
            w = font.measure(word[0])
            emoji_code = "-".join([format(ord(letter), "X") for letter in word])
            emoji_picture = self.emoji_cache.get(emoji_code)
            if emoji_picture:
                self.display_list.append((self.cursor_x, self.cursor_y, emoji_picture))
        else:
            w = font.measure(word)
            self.line.append((self.cursor_x, word, font))
        self.cursor_x += w + font.measure(" ")
        if self.cursor_x + w >= self.width - HSTEP:
            self.flush()

    def flush(self):
        if not self.line:
            return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))

        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

        self.cursor_x = HSTEP
        self.line = []
