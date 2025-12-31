import pytest
import tkinter
from soyorin.lexer import HTMLParser, Element
from soyorin.layout import DocumentLayout


@pytest.fixture(scope="session", autouse=True)
def tk_root():
    """Create a tkinter root window for the test session."""
    root = tkinter.Tk()
    root.withdraw()  # Hide the window
    yield root
    root.destroy()


def collect_layout_tags(layout_node):
    """Recursively collect all tags from the layout tree."""
    tags = []
    if hasattr(layout_node, "node") and isinstance(layout_node.node, Element):
        tags.append(layout_node.node.tag)

    if hasattr(layout_node, "children"):
        for child in layout_node.children:
            tags.extend(collect_layout_tags(child))

    return tags


def collect_html_tags(html_node):
    """Recursively collect all tags from the HTML tree."""
    tags = []
    if isinstance(html_node, Element):
        tags.append(html_node.tag)
        for child in html_node.children:
            tags.extend(collect_html_tags(child))

    return tags


"""
Test for Exercise 5-2: Hidden head

Verifies that <head> elements and their contents are:
1. Present in the HTML tree (HTMLParser output)
2. Excluded from the layout tree (BlockLayout tree)
"""


class TestExercise5_2:
    """Test suite for Exercise 5-2: Hidden head element."""

    def test_head_in_html_tree(self):
        """Verify that <head> exists in the HTML tree."""
        html = """
        <html>
            <head>
                <title>Test Page</title>
            </head>
            <body>
                <p>Content</p>
            </body>
        </html>
        """
        parser = HTMLParser(html)
        html_tree = parser.parse()

        html_tags = collect_html_tags(html_tree)

        assert "head" in html_tags, "head tag should be in HTML tree"
        assert "title" in html_tags, "title tag should be in HTML tree"

    def test_head_not_in_layout_tree(self):
        """Verify that <head> is excluded from the layout tree."""
        html = """
        <html>
            <head>
                <title>Test Page</title>
            </head>
            <body>
                <p>Content</p>
            </body>
        </html>
        """
        parser = HTMLParser(html)
        html_tree = parser.parse()

        layout = DocumentLayout(html_tree)
        layout.layout()

        layout_tags = collect_layout_tags(layout)

        assert "head" not in layout_tags, "head tag should NOT be in layout tree"
        assert "title" not in layout_tags, "title tag should NOT be in layout tree"
        assert "body" in layout_tags, "body tag should be in layout tree"
        assert "p" in layout_tags, "p tag should be in layout tree"

    def test_head_children_excluded(self):
        """Verify that all common head children are excluded from layout tree."""
        html = """
        <html>
            <head>
                <title>Test Page</title>
                <meta charset="UTF-8">
                <link rel="stylesheet" href="style.css">
                <script src="script.js"></script>
                <style>body { color: red; }</style>
            </head>
            <body>
                <h1>Heading</h1>
                <p>Paragraph</p>
            </body>
        </html>
        """
        parser = HTMLParser(html)
        html_tree = parser.parse()

        # Verify head children are in HTML tree
        html_tags = collect_html_tags(html_tree)
        assert "head" in html_tags
        assert "title" in html_tags
        assert "meta" in html_tags
        assert "link" in html_tags
        assert "script" in html_tags
        assert "style" in html_tags

        # Verify head children are NOT in layout tree
        layout = DocumentLayout(html_tree)
        layout.layout()
        layout_tags = collect_layout_tags(layout)

        assert "head" not in layout_tags, "head should not be in layout tree"
        assert "title" not in layout_tags, "title should not be in layout tree"
        assert "meta" not in layout_tags, "meta should not be in layout tree"
        assert "link" not in layout_tags, "link should not be in layout tree"
        assert "script" not in layout_tags, "script should not be in layout tree"
        assert "style" not in layout_tags, "style should not be in layout tree"

        # Body content should still be present
        assert "h1" in layout_tags, "h1 should be in layout tree"
        assert "p" in layout_tags, "p should be in layout tree"

    def test_multiple_head_elements(self):
        """Test edge case: multiple head elements (malformed HTML)."""
        html = """
        <html>
            <head>
                <title>First Title</title>
            </head>
            <head>
                <title>Second Title</title>
            </head>
            <body>
                <p>Content</p>
            </body>
        </html>
        """
        parser = HTMLParser(html)
        html_tree = parser.parse()

        layout = DocumentLayout(html_tree)
        layout.layout()
        layout_tags = collect_layout_tags(layout)

        # No head tags should appear in layout tree
        assert "head" not in layout_tags
        assert "title" not in layout_tags
        assert "p" in layout_tags

    def test_nested_head_elements(self):
        """Test that nested elements within head are also excluded."""
        html = """
        <html>
            <head>
                <title>Title with <b>bold</b> text</title>
                <script>
                    function test() {
                        console.log("test");
                    }
                </script>
            </head>
            <body>
                <p>Normal <b>bold</b> text</p>
            </body>
        </html>
        """
        parser = HTMLParser(html)
        html_tree = parser.parse()

        layout = DocumentLayout(html_tree)
        layout.layout()
        layout_tags = collect_layout_tags(layout)

        # head and its descendants should not be in layout
        assert "head" not in layout_tags
        assert "title" not in layout_tags
        assert "script" not in layout_tags

        # body content should be present
        assert "p" in layout_tags
        # Note: 'b' tag might appear in layout tree from the body paragraph

    def test_implicit_head_creation(self):
        """Test that implicitly created head elements are also excluded."""
        html = """
        <title>Implicit Head</title>
        <p>Content</p>
        """
        parser = HTMLParser(html)
        html_tree = parser.parse()

        # HTMLParser should implicitly create html, head, and body tags
        html_tags = collect_html_tags(html_tree)
        assert "html" in html_tags
        assert "head" in html_tags
        assert "body" in html_tags
        assert "title" in html_tags

        layout = DocumentLayout(html_tree)
        layout.layout()
        layout_tags = collect_layout_tags(layout)

        # Implicit head should also be excluded
        assert "head" not in layout_tags
        assert "title" not in layout_tags
        assert "p" in layout_tags

    def test_empty_head(self):
        """Test that empty head element is excluded."""
        html = """
        <html>
            <head></head>
            <body>
                <p>Content</p>
            </body>
        </html>
        """
        parser = HTMLParser(html)
        html_tree = parser.parse()

        layout = DocumentLayout(html_tree)
        layout.layout()
        layout_tags = collect_layout_tags(layout)

        assert "head" not in layout_tags
        assert "p" in layout_tags

    def test_head_with_text_content(self):
        """Test that text content within head is also excluded."""
        html = """
        <html>
            <head>
                Some random text in head
                <title>Title</title>
                More text
            </head>
            <body>
                <p>Body content</p>
            </body>
        </html>
        """
        parser = HTMLParser(html)
        html_tree = parser.parse()

        layout = DocumentLayout(html_tree)
        layout.layout()
        layout_tags = collect_layout_tags(layout)

        # head should not be in layout tree
        assert "head" not in layout_tags
        assert "title" not in layout_tags
        assert "p" in layout_tags
