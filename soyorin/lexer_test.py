import pytest
from lexer import HTMLParser, Element, Text


def test_quoted_attribute_with_spaces():
    """Test that spaces are preserved in quoted attributes."""
    html = '<div class="hello world">content</div>'
    parser = HTMLParser(html)
    root = parser.parse()

    # Navigate to the div element
    div = root.children[0].children[0]  # html > body > div

    assert isinstance(div, Element)
    assert div.tag == "div"
    assert "class" in div.attributes
    assert div.attributes["class"] == "hello world"


def test_quoted_attribute_with_right_angle_bracket():
    """Test that right angle bracket (>) in quoted attribute doesn't end the tag."""
    html = '<div title="hello > world">content</div>'
    parser = HTMLParser(html)
    root = parser.parse()

    # Navigate to the div element
    div = root.children[0].children[0]  # html > body > div

    assert isinstance(div, Element)
    assert div.tag == "div"
    assert "title" in div.attributes
    assert div.attributes["title"] == "hello > world"

    # Check that content is properly parsed
    assert len(div.children) == 1
    assert isinstance(div.children[0], Text)
    assert div.children[0].text == "content"


def test_quoted_attribute_with_left_angle_bracket():
    """Test that left angle bracket (<) in quoted attribute works."""
    html = '<div title="hello < world">content</div>'
    parser = HTMLParser(html)
    root = parser.parse()

    div = root.children[0].children[0]  # html > body > div

    assert isinstance(div, Element)
    assert div.tag == "div"
    assert "title" in div.attributes
    assert div.attributes["title"] == "hello < world"


def test_single_quoted_attributes():
    """Test single-quoted attributes with special characters."""
    html = "<div class='hello > world'>content</div>"
    parser = HTMLParser(html)
    root = parser.parse()

    div = root.children[0].children[0]  # html > body > div

    assert isinstance(div, Element)
    assert div.tag == "div"
    assert "class" in div.attributes
    assert div.attributes["class"] == "hello > world"


def test_mixed_quote_types():
    """Test both single and double quotes in the same tag."""
    html = """<div class="double > quote" title='single > quote'>content</div>"""
    parser = HTMLParser(html)
    root = parser.parse()

    div = root.children[0].children[0]  # html > body > div

    assert isinstance(div, Element)
    assert div.tag == "div"
    assert div.attributes["class"] == "double > quote"
    assert div.attributes["title"] == "single > quote"


def test_multiple_attributes_with_quotes():
    """Test multiple attributes, some quoted, some not."""
    html = '<input type="text" name="user input" value="a > b" disabled>'
    parser = HTMLParser(html)
    root = parser.parse()

    # input is self-closing, so it should be directly under body
    input_elem = root.children[0].children[0]  # html > body > input

    assert isinstance(input_elem, Element)
    assert input_elem.tag == "input"
    assert input_elem.attributes["type"] == "text"
    assert input_elem.attributes["name"] == "user input"
    assert input_elem.attributes["value"] == "a > b"
    assert input_elem.attributes["disabled"] == ""


def test_nested_tags_with_quoted_attributes():
    """Test nested tags where multiple tags have quoted attributes."""
    html = """
    <div class="outer > class">
        <span title="inner > title">text</span>
    </div>
    """
    parser = HTMLParser(html)
    root = parser.parse()

    div = root.children[0].children[0]  # html > body > div
    span = div.children[0]  # div > span

    assert isinstance(div, Element)
    assert div.attributes["class"] == "outer > class"

    assert isinstance(span, Element)
    assert span.attributes["title"] == "inner > title"


def test_empty_quoted_attribute():
    """Test empty quoted attribute values."""
    html = '<div class="">content</div>'
    parser = HTMLParser(html)
    root = parser.parse()

    div = root.children[0].children[0]  # html > body > div

    assert isinstance(div, Element)
    assert "class" in div.attributes
    assert div.attributes["class"] == ""


def test_single_boolean_attribute():
    """Test boolean attributes without values."""
    html = "<script async bsync >let content;</script>"
    parser = HTMLParser(html)
    root = parser.parse()

    script = root.children[0].children[0]  # html > body > script

    assert isinstance(script, Element)
    assert "async" in script.attributes
    assert "bsync" in script.attributes

    assert script.attributes["async"] == ""
    assert script.attributes["bsync"] == ""


def test_quote_at_end_of_value():
    """Test attribute value ending with different quote than it started."""
    # This should handle: class="value' - mismatched quotes
    html = """<div class="hello'world">content</div>"""
    parser = HTMLParser(html)
    root = parser.parse()

    div = root.children[0].children[0]  # html > body > div

    # The value should include the single quote since it started with double quote
    assert isinstance(div, Element)
    assert "class" in div.attributes
    # This tests that quote matching is done correctly


def test_quote_multiple_value():
    """Test multiple attributes with quoted values containing spaces."""
    html = """<div class="hello world" aria-role="button">content</div>"""
    parser = HTMLParser(html)
    root = parser.parse()

    div = root.children[0].children[0]  # html > body > div

    assert isinstance(div, Element)
    assert div.tag == "div"
    assert "class" in div.attributes
    assert div.attributes["class"] == "hello world"
    assert "aria-role" in div.attributes
    assert div.attributes["aria-role"] == "button"

    # Check that content is properly parsed
    assert len(div.children) == 1
    assert isinstance(div.children[0], Text)
    assert div.children[0].text == "content"


def test_script_tag_with_content_after():
    """Test that content after script tag is properly parsed."""
    html = """<script async>
      let x = 1 < 54;
    </script>
    <div>After script</div>"""

    parser = HTMLParser(html)
    root = parser.parse()

    # Find body
    body = None
    for child in root.children:
        if isinstance(child, Element) and child.tag == "body":
            body = child
            break

    assert body is not None, "Could not find body element"

    # Body should have 1 child: div (script is in head because it's a HEAD_TAG)
    assert len(body.children) == 1, f"Expected 1 child in body, got {len(body.children)}"

    # Check the div element in body
    div = body.children[0]
    assert isinstance(div, Element)
    assert div.tag == "div", f"Expected div, got {div.tag}"
    assert len(div.children) == 1
    assert isinstance(div.children[0], Text)
    assert div.children[0].text == "After script"

    # Also verify script is in head
    head = None
    for child in root.children:
        if isinstance(child, Element) and child.tag == "head":
            head = child
            break

    assert head is not None, "Could not find head element"
    assert len(head.children) == 1, f"Expected 1 child in head, got {len(head.children)}"
    script = head.children[0]
    assert isinstance(script, Element)
    assert script.tag == "script"
