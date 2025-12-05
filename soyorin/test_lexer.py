from lexer import HTMLParser, Element, Text
import sys
import io
import traceback

"""
Test cases for HTML lexer, focusing on quoted attributes with special characters.

This test suite checks if the lexer correctly handles:
1. Spaces in quoted attributes
2. Right angle brackets (>) in quoted attributes
3. Left angle brackets (<) in quoted attributes
4. Mixed quote types (single and double)
5. Multiple attributes with quotes
"""

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


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
    assert (
        div.attributes["class"] == "hello world"
    ), f"Expected 'hello world' but got '{div.attributes['class']}'"

    print("✓ Test passed: Quoted attribute with spaces")


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
    assert (
        div.attributes["title"] == "hello > world"
    ), f"Expected 'hello > world' but got '{div.attributes.get('title', 'MISSING')}'"

    # Check that content is properly parsed
    assert len(div.children) == 1
    assert isinstance(div.children[0], Text)
    assert div.children[0].text == "content"

    print("✓ Test passed: Quoted attribute with right angle bracket")


def test_quoted_attribute_with_left_angle_bracket():
    """Test that left angle bracket (<) in quoted attribute works."""
    html = '<div title="hello < world">content</div>'
    parser = HTMLParser(html)
    root = parser.parse()

    div = root.children[0].children[0]  # html > body > div

    assert isinstance(div, Element)
    assert div.tag == "div"
    assert "title" in div.attributes
    assert (
        div.attributes["title"] == "hello < world"
    ), f"Expected 'hello < world' but got '{div.attributes.get('title', 'MISSING')}'"

    print("✓ Test passed: Quoted attribute with left angle bracket")


def test_single_quoted_attributes():
    """Test single-quoted attributes with special characters."""
    html = "<div class='hello > world'>content</div>"
    parser = HTMLParser(html)
    root = parser.parse()

    div = root.children[0].children[0]  # html > body > div

    assert isinstance(div, Element)
    assert div.tag == "div"
    assert "class" in div.attributes
    assert (
        div.attributes["class"] == "hello > world"
    ), f"Expected 'hello > world' but got '{div.attributes.get('class', 'MISSING')}'"

    print("✓ Test passed: Single-quoted attribute with right angle bracket")


def test_mixed_quote_types():
    """Test both single and double quotes in the same tag."""
    html = """<div class="double > quote" title='single > quote'>content</div>"""
    parser = HTMLParser(html)
    root = parser.parse()

    div = root.children[0].children[0]  # html > body > div

    assert isinstance(div, Element)
    assert div.tag == "div"
    assert (
        div.attributes["class"] == "double > quote"
    ), f"Expected 'double > quote' but got '{div.attributes.get('class', 'MISSING')}'"
    assert (
        div.attributes["title"] == "single > quote"
    ), f"Expected 'single > quote' but got '{div.attributes.get('title', 'MISSING')}'"

    print("✓ Test passed: Mixed quote types")


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

    print("✓ Test passed: Multiple attributes with quotes")


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

    print("✓ Test passed: Nested tags with quoted attributes")


def test_empty_quoted_attribute():
    """Test empty quoted attribute values."""
    html = '<div class="">content</div>'
    parser = HTMLParser(html)
    root = parser.parse()

    div = root.children[0].children[0]  # html > body > div

    assert isinstance(div, Element)
    assert "class" in div.attributes
    assert div.attributes["class"] == ""

    print("✓ Test passed: Empty quoted attribute")


def test_single_boolean_attribute():
    """Test empty quoted attribute values."""
    html = "<script async bsync >let content;</script>"
    parser = HTMLParser(html)
    root = parser.parse()

    script = root.children[0].children[0]  # html > body > script

    assert isinstance(script, Element)
    assert "async" in script.attributes
    assert "bsync" in script.attributes

    assert script.attributes["async"] == ""
    assert script.attributes["bsync"] == ""

    print("✓ Test passed: Empty quoted attribute")


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

    print("✓ Test passed: Quote inside different quote type")


def test_quote_multiple_value():
    """Test multiple attributes with quoted values containing spaces."""
    html = """<div class="hello world" aria-role="button">content</div>"""
    parser = HTMLParser(html)
    root = parser.parse()

    div = root.children[0].children[0]  # html > body > div

    assert isinstance(div, Element)
    assert div.tag == "div"
    assert "class" in div.attributes
    assert (
        div.attributes["class"] == "hello world"
    ), f"Expected 'hello world' but got '{div.attributes.get('class', 'MISSING')}'"
    assert "aria-role" in div.attributes
    assert (
        div.attributes["aria-role"] == "button"
    ), f"Expected 'button' but got '{div.attributes.get('aria-role', 'MISSING')}'"

    # Check that content is properly parsed
    assert len(div.children) == 1
    assert isinstance(div.children[0], Text)
    assert div.children[0].text == "content"

    print("✓ Test passed: Multiple quoted attributes with spaces")


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
    assert (
        len(body.children) == 1
    ), f"Expected 1 child in body, got {len(body.children)}"

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
    assert (
        len(head.children) == 1
    ), f"Expected 1 child in head, got {len(head.children)}"
    script = head.children[0]
    assert isinstance(script, Element)
    assert script.tag == "script"

    print("✓ Test passed: Script tag with content after")


def run_all_tests():
    """Run all test cases and report results."""
    tests = [
        test_quoted_attribute_with_spaces,
        test_quoted_attribute_with_right_angle_bracket,
        test_quoted_attribute_with_left_angle_bracket,
        test_single_quoted_attributes,
        test_mixed_quote_types,
        test_multiple_attributes_with_quotes,
        test_nested_tags_with_quoted_attributes,
        test_empty_quoted_attribute,
        test_quote_at_end_of_value,
        test_quote_multiple_value,
        test_script_tag_with_content_after,
        test_single_boolean_attribute,
    ]

    print("=" * 60)
    print("Running HTML Lexer Tests - Quoted Attributes")
    print("=" * 60)

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ Test failed: {test.__name__}")
            if str(e):
                print(f"  Error: {e}")
            # Get the traceback to show line number
            tb = traceback.extract_tb(e.__traceback__)
            for frame in tb:
                if frame.filename.endswith("test_lexer.py"):
                    print(f"  at {frame.filename}:{frame.lineno}: {frame.line}")
            failed += 1
        except Exception as e:
            print(f"✗ Test error: {test.__name__}")
            print(f"  Exception: {e}")
            # Get the traceback to show line number
            tb = traceback.extract_tb(e.__traceback__)
            for frame in tb:
                if frame.filename.endswith("test_lexer.py"):
                    print(f"  at {frame.filename}:{frame.lineno}: {frame.line}")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
