import tkinter
from tkinter import Label
from tkinter.font import Font
from typing import Literal

FONTS: dict[
    tuple[int, Literal["normal", "bold"], Literal["roman", "italic"], str],
    tuple[Font, Label],
] = {}


def get_font(
    size: int,
    weight: Literal["normal", "bold"],
    style: Literal["roman", "italic"],
    family: str = "D2Coding",
) -> Font:
    size = int(size)  # Ensure size is always an integer
    key = (size, weight, style, family)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=style, family=family)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]
