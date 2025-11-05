from soyorin.emoji import EmojiCache
import tkinter
from typing import Tuple


class Layout:

    def __init__(self, width: int, height: int, hstep: int, vstep: int):
        self.width = width
        self.height = height
        self.hstep = hstep
        self.vstep = vstep

        self.content_height = hstep
        self.emoji_cache = EmojiCache()

    def layout(self, text: str):
        display_list: list[Tuple[float, float, tkinter.PhotoImage | str]] = []
        self.content_height = self.vstep

        cursor_x, cursor_y = self.hstep, self.vstep
        idx = 0
        while idx < len(text):
            c = text[idx]
            # 연습문제 2-1 줄바꿈
            if c == "\n":
                cursor_y += self.vstep
                cursor_x = self.hstep
                idx += 1
                continue

            curr_code = format(ord(c), "X")

            best_match = self.emoji_cache.get(curr_code)
            best_match_length = 0

            emoji_codes = [curr_code]
            for jdx in range(1, 11):
                if idx + jdx >= len(text):
                    break
                curr_code = format(ord(text[idx + jdx]), "X")
                emoji_codes.append(curr_code)

                combined_code = "-".join(emoji_codes)
                emoji = self.emoji_cache.get(combined_code)

                if emoji is not None:
                    best_match = emoji
                    best_match_length = jdx

            if best_match is not None:
                display_list.append((cursor_x, cursor_y, best_match))
                idx += best_match_length + 1
            else:
                display_list.append((cursor_x, cursor_y, c))
                idx += 1

            cursor_x += self.hstep
            if cursor_x >= self.width - self.hstep:
                cursor_y += self.vstep
                cursor_x = self.hstep
        self.content_height = cursor_y

        return display_list
