from dataclasses import dataclass


@dataclass
class Text:
    text: str


@dataclass
class Tag:
    tag: str


class Lexer:
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
            # Don't forget any remaining text after the last tag
            if buffer and not in_tag:
                buffer = buffer.replace("&lt;", "<")
                buffer = buffer.replace("&gt;", ">")
                out.append(Text(buffer))
        print(out)
        return out
