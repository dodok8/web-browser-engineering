from soyorin.emoji import EmojiCache
import tkinter
import tkinter.font
from typing import Tuple
import regex


class Layout:

    def __init__(self, width: float, height: float, hstep: float, vstep: float):
        self.width = width
        self.height = height
        self.hstep = hstep
        self.vstep = vstep

        self.content_height = hstep
        self.emoji_cache = EmojiCache()

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

    def layout(self, text: str):
        display_list: list[Tuple[float, float, tkinter.PhotoImage | str]] = []
        self.content_height = self.vstep
        font = tkinter.font.Font()
        cursor_x, cursor_y = self.hstep, self.vstep
        for is_emoji, word in self.split_text_and_emojis(text):
            if is_emoji:
                w = font.measure(word[0])
                emoji_code = "-".join([format(ord(letter), "X") for letter in word])
                emoji_picture = self.emoji_cache.get(emoji_code)
                if emoji_picture:
                    display_list.append((cursor_x, cursor_y, emoji_picture))
            else:
                w = font.measure(word)
                display_list.append((cursor_x, cursor_y, word))
            cursor_x += w + font.measure(" ")
            if cursor_x + w >= self.width - self.hstep:
                cursor_y += font.metrics("linespace") * 1.25
                cursor_x = self.hstep
        self.content_height = cursor_y

        return display_list
