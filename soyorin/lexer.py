from __future__ import annotations

type Token = Text | Element

SELF_CLOSING_TAGS = [
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
]


class Text:
    def __init__(self, text: str, parent: Element):
        self.text = text
        self.children = []
        self.parent = parent

    def __repr__(self):
        return repr(self.text)


class Element:

    def __init__(self, tag: str, attributes: dict[str, str], parent: Element | None):
        self.tag = tag
        self.attributes = attributes
        self.children: list[Token] = []
        self.parent = parent

    def __repr__(self):
        return f"<{self.tag}>"


class HTMLParser:
    HEAD_TAGS = [
        "base",
        "basefront",
        "bgsound",
        "noscript",
        "link",
        "meta",
        "title",
        "style",
        "script",
    ]

    def __init__(self, body: str):
        self.body = body
        self.unfinished: list[Element] = []

    def parse(self):
        text = ""
        in_tag = False
        in_script = False
        idx = 0

        while idx < len(self.body):
            c = self.body[idx]
            if self.body[idx : idx + 4] == "<!--":
                comment_end = self.body.find("-->", idx + 4)

                if comment_end == -1:
                    break
                else:
                    idx = comment_end + 3
                    continue

            if in_script:
                if self.body[idx : idx + 9] == "</script>":
                    if text:
                        self.add_text(text)
                        text = ""
                    in_script = False
                    in_tag = False
                    idx += 9
                    continue
                else:
                    text += c
                    idx += 1
                    continue

            if c == "<":
                in_tag = True
                if text:
                    self.add_text(text)
                text = ""
            elif c == ">":
                in_tag = False
                self.add_tag(text)
                if text.split()[0] == "script":
                    in_script = True
                text = ""
            else:
                text += c
            idx += 1
        if not in_tag and text:
            self.add_text(text)
        return self.finish()

    def add_text(self, text: str):
        if text.isspace():
            return
        self.implicit_tags(None)
        parent = self.unfinished[-1]
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        node = Text(text, parent)
        parent.children.append(node)

    def add_tag(self, tag: str):
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"):
            return
        self.implicit_tags(tag)
        if tag.startswith("/"):
            # 닫는 태그
            if len(self.unfinished) == 1:
                return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        elif tag in SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, attributes, parent)
            parent.children.append(node)
        else:
            # 여는 태그
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)

    def finish(self):
        if not self.unfinished:
            self.implicit_tags(None)
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()

    def get_attributes(self, text: str):
        parts_list = text.split(maxsplit=1)
        tag = parts_list[0].casefold()
        parts = parts_list[1] if len(parts_list) > 1 else ""
        attributes: dict[str, str] = {}

        key = ""
        value = ""
        in_quote = False
        idx = 0
        while idx < len(parts):
            c = parts[idx]
            if c == " " and not in_quote:
                attributes[key.casefold()] = value
                idx += 1
                key = ""
                value = ""
            elif c == "=":
                in_quote = True
                idx += 2
            elif c == "'" or c == '"':
                in_quote = False
                idx += 1
            else:
                if in_quote:
                    value += c
                    idx += 1
                else:
                    key += c
                    idx += 1
        if key != "":
            attributes[key.casefold()] = value
        print(attributes)
        return tag, attributes

    def implicit_tags(self, tag):
        while True:
            open_tags = [node.tag for node in self.unfinished]

            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] and tag not in ["head", "body", "/html"]:
                if tag in self.HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            elif (
                open_tags == ["html", "head"] and tag not in ["/head"] + self.HEAD_TAGS
            ):
                self.add_tag("/head")
            else:
                break


def print_tree(node: Token, indent=0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)
