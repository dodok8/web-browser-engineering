from abc import ABC, abstractmethod
from dataclasses import dataclass
from tkinter import Canvas
from tkinter.font import Font


@dataclass
class Rect:
    left: float
    top: float
    right: float
    bottom: float

    def contains_point(self, x, y):
        return x >= self.left and x < self.right and y >= self.top and y < self.bottom


class DrawCommand(ABC):
    """Abstract base class for draw commands"""

    @abstractmethod
    def execute(self, scroll: float, canvas: Canvas) -> None:
        """Execute the draw command with given scroll offset and canvas"""
        pass


class DrawText(DrawCommand):
    def __init__(self, x1: float, y1: float, text: str, font: Font, color: str):
        self.rect = Rect(
            x1, y1, x1 + font.measure(text), y1 + font.metrics("linespace")
        )
        self.top: float = y1
        self.left: float = x1
        self.text: str = text
        self.font: Font = font
        self.color: str = color
        self.bottom: float = y1 + font.metrics("linespace")

    def execute(self, scroll: float, canvas: Canvas) -> None:
        canvas.create_text(
            self.left,
            self.top - scroll,
            text=self.text,
            font=self.font,
            anchor="nw",
            fill=self.color,
        )


class DrawRect(DrawCommand):
    def __init__(self, rect: Rect, color: str = "black"):
        self.rect: Rect = rect
        self.top: float = rect.top
        self.left: float = rect.left
        self.bottom: float = rect.bottom
        self.right: float = rect.right
        self.color: str = color

    def execute(self, scroll: float, canvas: Canvas) -> None:
        canvas.create_rectangle(
            self.left,
            self.top - scroll,
            self.right,
            self.bottom - scroll,
            width=0,
            fill=self.color,
        )


class DrawOutline(DrawCommand):
    def __init__(self, rect: Rect, color: str, thickness: int):
        self.rect: Rect = rect
        self.color: str = color
        self.thickness: int = thickness

    def execute(self, scroll: float, canvas: Canvas) -> None:
        canvas.create_rectangle(
            self.rect.left,
            self.rect.top - scroll,
            self.rect.right,
            self.rect.bottom - scroll,
            width=self.thickness,
            outline=self.color,
        )


class DrawLine(DrawCommand):
    def __init__(
        self, x1: float, y1: float, x2: float, y2: float, color: str, thickness: int
    ):
        self.rect: Rect = Rect(x1, y1, x2, y2)
        self.color: str = color
        self.thickness: int = thickness

    def execute(self, scroll: float, canvas: Canvas) -> None:
        canvas.create_line(
            self.rect.left,
            self.rect.top - scroll,
            self.rect.right,
            self.rect.bottom - scroll,
            fill=self.color,
            width=self.thickness,
        )
