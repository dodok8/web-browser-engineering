from typing import Optional
from typing import Dict
import tkinter
import os
from pathlib import Path


class EmojiCache:
    def __init__(self):
        self.emoji_cache: Dict[str, Optional[tkinter.PhotoImage]] = dict()

        max_len = 0
        emoji_path = Path(__file__).parent.parent / "emoji"
        for emoji_file_name in os.listdir(emoji_path):
            multi_emoji_code = emoji_file_name.strip(".png")

            max_len = max(max_len, len(multi_emoji_code.split("-")))
            self.emoji_cache[multi_emoji_code] = None
        print(f"max_len: {max_len}")

    def get(self, emoji_code: str):
        if emoji_code in self.emoji_cache:
            if self.emoji_cache[emoji_code] is None:
                self.emoji_cache[emoji_code] = tkinter.PhotoImage(
                    file=f"emoji/{emoji_code}.png"
                )

            return self.emoji_cache[emoji_code]
        else:
            return None
