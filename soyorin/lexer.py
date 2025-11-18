from __future__ import annotations

type Token = Text | Tag


class Text:
    def __init__(self, text: str, parent: Tag):
        self.text = text
        self.children = []
        self.parent = parent


class Tag:
    def __init__(self, tag: str, parent: Tag):
        self.tag = tag
        self.children: list[Token] = []
        self.parent = parent


class HTMLParser:
    def __init__(self, body: str):
        self.body = body
        self.unfinished = []

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

    def lex(self, body: str, view_source: bool):
        if view_source:
            out: list[Text | Tag] = [Text(body)]
            return out
        else:
            out: list[Text | Tag] = []
            buffer = ""
            in_tag = False
            for c in body:
                if c == "<":
                    in_tag = True
                    if buffer:
                        buffer = buffer.replace("&lt;", "<")
                        buffer = buffer.replace("&gt;", ">")
                        out.append(Text(buffer))
                    buffer = ""
                elif c == ">":
                    in_tag = False
                    out.append(Tag(buffer))
                    buffer = ""
                else:
                    buffer += c
            if buffer and not in_tag:
                buffer = buffer.replace("&lt;", "<")
                buffer = buffer.replace("&gt;", ">")
                out.append(Text(buffer))
        return out
