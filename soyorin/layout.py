from typing import Tuple


class Layout:

    def __init__(self, width: int, height: int, hstep: int, vstep: int):
        self.width = width
        self.height = height
        self.hstep = hstep
        self.vstep = vstep
        self.display_list: list[Tuple[int, int, str]] = []

        self.content_height = hstep

    def update_layout(self, text):
        self.display_list = []
        self.content_height = self.vstep
        cursor_x, cursor_y = self.hstep, self.vstep
        for c in text:
            # 연습문제 2-1 줄바꿈
            if c == "\n":
                cursor_y += self.vstep
                cursor_x = self.hstep
            self.display_list.append((cursor_x, cursor_y, c))

            cursor_x += self.hstep
            if cursor_x >= self.width - self.hstep:
                cursor_y += self.vstep
                cursor_x = self.hstep

        self.content_height = cursor_y
