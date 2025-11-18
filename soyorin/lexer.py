from __future__ import annotations

type Token = Text | Element


class Text:
    def __init__(self, text: str, parent: Element):
        self.text = text
        self.children = []
        self.parent = parent


class Element:
    def __init__(self, tag: str, parent: Element | None):
        self.tag = tag
        self.children: list[Token] = []
        self.parent = parent


class HTMLParser:
    def __init__(self, body: str):
        self.body = body
        self.unfinished: list[Element] = []

    def prase(self):
        text = ""
        in_tag = False
        for c in self.body:
            if c == "<":
                in_tag = True
                if text:
                    self.add_text(text)  # 여기서 엔티티 처리하면 되겠다.
                text = ""
            elif c == ">":
                in_tag = False
                self.add_tag(text)
                text = ""
            else:
                text += c
        if not in_tag and text:
            self.add_text(text)
        return self.finish()

    def add_text(self, text: str):
        parent = self.unfinished[-1]
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        node = Text(text, parent)
        parent.children.append(node)

    def add_tag(self, tag: str):
        if tag.startswith("/"):
            # 닫는 태그
            if len(self.unfinished) == 1:
                return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        else:
            # 여는 태그
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, parent)
            self.unfinished.append(node)

    def finish(self):
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()
