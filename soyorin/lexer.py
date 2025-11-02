class Lexer:
    def __is_rtl_char(self, c):
        code = ord(c)
        return (
            0x0590 <= code <= 0x05FF  # Hebrew
            or 0x0600 <= code <= 0x06FF  # Arabic
            or 0x0750 <= code <= 0x077F  # Arabic Supplement
            or 0x08A0 <= code <= 0x08FF  # Arabic Extended-A
            or 0xFB50 <= code <= 0xFDFF  # Arabic Presentation Forms-A
            or 0xFE70 <= code <= 0xFEFF  # Arabic Presentation Forms-B
        )

    def lex(self, body: str, view_source: bool):
        if view_source:
            text = body
        else:
            in_tag = False
            text = ""
            for c in body:
                if c == "<":
                    in_tag = True
                elif c == ">":
                    in_tag = False
                elif not in_tag:
                    text += c
            text = text.replace("&lt;", "<")
            text = text.replace("&gt;", ">")
        return text
