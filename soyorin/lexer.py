class Lexer:
    def lex(self, body: str, view_source: bool):
        if view_source:
            return body
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
