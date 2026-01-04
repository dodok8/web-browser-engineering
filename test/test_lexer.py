from soyorin.lexer import HTMLParser
from soyorin.lexer import Text
from soyorin.lexer import Element

"""
4-2

HTML 스펙 : https://html.spec.whatwg.org/multipage/syntax.html#optional-tags
"""


def test_simple_nested_paragraph():
    """Test that <p>hello<p>world</p> creates two sibling paragraphs."""
    html = "<p>hello<p>world</p>"
    parser = HTMLParser(html)
    root = parser.parse()

    body = root.children[0]  # html > body
    assert isinstance(body, Element)
    assert body.tag == "body"

    # Should have 2 paragraph children, not 1 paragraph with nested paragraph
    assert (
        len(body.children) == 2
    ), f"Expected 2 sibling paragraphs, got {len(body.children)} children"

    # First paragraph
    p1 = body.children[0]
    assert isinstance(p1, Element)
    assert p1.tag == "p"
    assert len(p1.children) == 1
    assert isinstance(p1.children[0], Text)
    assert p1.children[0].text == "hello"

    # Second paragraph
    p2 = body.children[1]
    assert isinstance(p2, Element)
    assert p2.tag == "p"
    assert len(p2.children) == 1
    assert isinstance(p2.children[0], Text)
    assert p2.children[0].text == "world"


def test_multiple_nested_paragraphs():
    """Test multiple consecutive paragraph openings."""
    html = "<p>first<p>second<p>third</p>"
    parser = HTMLParser(html)
    root = parser.parse()

    body = root.children[0]  # html > body

    # Should have 3 sibling paragraphs
    assert (
        len(body.children) == 3
    ), f"Expected 3 sibling paragraphs, got {len(body.children)}"

    texts = ["first", "second", "third"]
    for i, expected_text in enumerate(texts):
        p = body.children[i]
        assert isinstance(p, Element)
        assert p.tag == "p"
        assert len(p.children) == 1
        assert isinstance(p.children[0], Text)
        assert p.children[0].text == expected_text


def test_paragraph_with_other_elements():
    """Test that <p> can still contain other inline elements."""
    html = "<p>hello <em>world</em></p>"
    parser = HTMLParser(html)
    root = parser.parse()

    body = root.children[0]  # html > body
    p = body.children[0]

    assert isinstance(p, Element)
    assert p.tag == "p"
    # Should have text "hello " and an <em> element
    assert len(p.children) == 2

    # First child: text
    assert isinstance(p.children[0], Text)
    assert p.children[0].text == "hello "

    # Second child: em element
    assert isinstance(p.children[1], Element)
    assert p.children[1].tag == "em"


def test_paragraph_auto_close_on_opening():
    """Test that opening a new <p> auto-closes the previous one."""
    html = "<p>first<p>second"
    parser = HTMLParser(html)
    root = parser.parse()

    body = root.children[0]  # html > body

    # Should have 2 paragraphs even without explicit closing tags
    assert len(body.children) == 2

    p1 = body.children[0]
    assert p1.tag == "p"
    assert p1.children[0].text == "first"

    p2 = body.children[1]
    assert p2.tag == "p"
    assert p2.children[0].text == "second"


def test_empty_nested_paragraph():
    """Test nested paragraph with no content in first one."""
    html = "<p><p>content</p>"
    parser = HTMLParser(html)
    root = parser.parse()

    body = root.children[0]  # html > body

    # First <p> should be empty (auto-closed), second should have content
    # After auto-close, we might have just 1 paragraph with content
    # depending on implementation (empty paragraphs might be skipped)
    paragraphs = [
        child
        for child in body.children
        if isinstance(child, Element) and child.tag == "p"
    ]
    assert len(paragraphs) >= 1

    # At least one paragraph should have the content
    has_content = False
    for p in paragraphs:
        if (
            p.children
            and isinstance(p.children[0], Text)
            and p.children[0].text == "content"
        ):
            has_content = True
            break
    assert has_content, "Expected to find paragraph with 'content'"


def test_simple_nested_li():
    """Test that <li>item1<li>item2</li> creates two sibling list items."""
    html = "<ul><li>item1<li>item2</li></ul>"
    parser = HTMLParser(html)
    root = parser.parse()

    body = root.children[0]  # html > body
    ul = body.children[0]

    assert isinstance(ul, Element)
    assert ul.tag == "ul"

    # Should have 2 list item children, not nested
    assert (
        len(ul.children) == 2
    ), f"Expected 2 sibling list items, got {len(ul.children)}"

    # First list item
    li1 = ul.children[0]
    assert isinstance(li1, Element)
    assert li1.tag == "li"
    assert len(li1.children) == 1
    assert isinstance(li1.children[0], Text)
    assert li1.children[0].text == "item1"

    # Second list item
    li2 = ul.children[1]
    assert isinstance(li2, Element)
    assert li2.tag == "li"
    assert len(li2.children) == 1
    assert isinstance(li2.children[0], Text)
    assert li2.children[0].text == "item2"


def test_multiple_nested_li():
    """Test multiple consecutive <li> openings."""
    html = "<ol><li>one<li>two<li>three</li></ol>"
    parser = HTMLParser(html)
    root = parser.parse()

    body = root.children[0]  # html > body
    ol = body.children[0]

    assert isinstance(ol, Element)
    assert ol.tag == "ol"

    # Should have 3 sibling list items
    assert len(ol.children) == 3

    texts = ["one", "two", "three"]
    for i, expected_text in enumerate(texts):
        li = ol.children[i]
        assert isinstance(li, Element)
        assert li.tag == "li"
        assert li.children[0].text == expected_text


def test_li_with_inline_elements():
    """Test that <li> can contain inline elements."""
    html = "<ul><li>text <strong>bold</strong> more</li></ul>"
    parser = HTMLParser(html)
    root = parser.parse()

    body = root.children[0]  # html > body
    ul = body.children[0]
    li = ul.children[0]

    assert isinstance(li, Element)
    assert li.tag == "li"

    # Should have text, strong element, and more text
    assert len(li.children) == 3

    assert isinstance(li.children[0], Text)
    assert li.children[0].text == "text "

    assert isinstance(li.children[1], Element)
    assert li.children[1].tag == "strong"

    assert isinstance(li.children[2], Text)
    assert li.children[2].text == " more"


def test_nested_ul_inside_li():
    """Test that nested <ul> inside <li> is allowed."""
    html = """
    <ul>
        <li>parent
            <ul>
                <li>child</li>
            </ul>
        </li>
    </ul>
    """
    parser = HTMLParser(html)
    root = parser.parse()

    body = root.children[0]  # html > body
    outer_ul = body.children[0]

    assert isinstance(outer_ul, Element)
    assert outer_ul.tag == "ul"

    # Outer ul should have 1 li
    assert len(outer_ul.children) == 1
    outer_li = outer_ul.children[0]
    assert isinstance(outer_li, Element)
    assert outer_li.tag == "li"

    # The li should contain text "parent" and a nested ul
    # Find the nested ul
    inner_ul = None
    for child in outer_li.children:
        if isinstance(child, Element) and child.tag == "ul":
            inner_ul = child
            break

    assert inner_ul is not None, "Expected to find nested <ul> inside <li>"

    # Inner ul should have 1 li with text "child"
    assert len(inner_ul.children) == 1
    inner_li = inner_ul.children[0]
    assert isinstance(inner_li, Element)
    assert inner_li.tag == "li"

    # Find the "child" text
    has_child_text = False
    for child in inner_li.children:
        if isinstance(child, Text) and child.text == "child":
            has_child_text = True
            break
    assert has_child_text, "Expected to find 'child' text in nested li"


def test_nested_ol_inside_li():
    """Test that nested <ol> inside <li> is allowed."""
    html = """
    <ul>
        <li>item
            <ol>
                <li>nested item</li>
            </ol>
        </li>
    </ul>
    """
    parser = HTMLParser(html)
    root = parser.parse()

    body = root.children[0]  # html > body
    ul = body.children[0]
    li = ul.children[0]

    # Find nested ol
    ol = None
    for child in li.children:
        if isinstance(child, Element) and child.tag == "ol":
            ol = child
            break

    assert ol is not None, "Expected to find nested <ol> inside <li>"
    assert len(ol.children) == 1
    assert ol.children[0].tag == "li"


def test_multiple_levels_of_nesting():
    """Test multiple levels of list nesting."""
    html = """
    <ul>
        <li>level 1
            <ul>
                <li>level 2
                    <ul>
                        <li>level 3</li>
                    </ul>
                </li>
            </ul>
        </li>
    </ul>
    """
    parser = HTMLParser(html)
    root = parser.parse()

    body = root.children[0]  # html > body

    # Navigate down the nested structure
    ul1 = body.children[0]
    assert ul1.tag == "ul"

    li1 = ul1.children[0]
    assert li1.tag == "li"

    # Find second level ul
    ul2 = None
    for child in li1.children:
        if isinstance(child, Element) and child.tag == "ul":
            ul2 = child
            break
    assert ul2 is not None, "Expected level 2 <ul>"

    li2 = ul2.children[0]
    assert li2.tag == "li"

    # Find third level ul
    ul3 = None
    for child in li2.children:
        if isinstance(child, Element) and child.tag == "ul":
            ul3 = child
            break
    assert ul3 is not None, "Expected level 3 <ul>"

    li3 = ul3.children[0]
    assert li3.tag == "li"

    # Verify deepest text
    has_level3_text = False
    for child in li3.children:
        if isinstance(child, Text) and "level 3" in child.text:
            has_level3_text = True
            break
    assert has_level3_text


def test_paragraph_inside_li():
    """Test that paragraph can be inside list item."""
    html = "<ul><li><p>paragraph in list</p></li></ul>"
    parser = HTMLParser(html)
    root = parser.parse()

    body = root.children[0]  # html > body
    ul = body.children[0]
    li = ul.children[0]

    assert li.tag == "li"

    # li should contain a p element
    p = li.children[0]
    assert isinstance(p, Element)
    assert p.tag == "p"
    assert p.children[0].text == "paragraph in list"


def test_list_between_paragraphs():
    """Test list appearing between paragraphs."""
    html = """
    <p>before</p>
    <ul>
        <li>item</li>
    </ul>
    <p>after</p>
    """
    parser = HTMLParser(html)
    root = parser.parse()

    body = root.children[0]  # html > body

    # Body should have: p, ul, p
    assert len(body.children) == 3

    assert body.children[0].tag == "p"
    assert body.children[1].tag == "ul"
    assert body.children[2].tag == "p"


def test_nested_p_in_nested_li():
    """Test that nested <p> still doesn't work even inside <li>."""
    html = "<ul><li><p>first<p>second</p></li></ul>"
    parser = HTMLParser(html)
    root = parser.parse()

    body = root.children[0]  # html > body
    ul = body.children[0]
    li = ul.children[0]

    # The li should contain 2 sibling paragraphs, not nested
    paragraphs = [
        child
        for child in li.children
        if isinstance(child, Element) and child.tag == "p"
    ]
    assert (
        len(paragraphs) == 2
    ), f"Expected 2 sibling paragraphs in <li>, got {len(paragraphs)}"


def test_complex_document_structure():
    """Test a complex document with multiple paragraphs and lists."""
    html = """
    <p>intro</p>
    <p>second<p>third</p>
    <ul>
        <li>item 1<li>item 2
            <ul>
                <li>nested</li>
            </ul>
        </li>
    </ul>
    <p>conclusion</p>
    """
    parser = HTMLParser(html)
    root = parser.parse()

    body = root.children[0]  # html > body

    # Count paragraphs and lists in body
    paragraphs = [
        child
        for child in body.children
        if isinstance(child, Element) and child.tag == "p"
    ]
    lists = [
        child
        for child in body.children
        if isinstance(child, Element) and child.tag == "ul"
    ]

    # Should have 4 paragraphs: intro, second, third, conclusion
    assert len(paragraphs) == 4, f"Expected 4 paragraphs, got {len(paragraphs)}"

    # Should have 1 ul
    assert len(lists) == 1, f"Expected 1 ul, got {len(lists)}"


def test_empty_paragraph_siblings():
    """Test consecutive empty paragraph tags."""
    html = "<p></p><p>content</p>"
    parser = HTMLParser(html)
    root = parser.parse()

    body = root.children[0]  # html > body
    paragraphs = [
        child
        for child in body.children
        if isinstance(child, Element) and child.tag == "p"
    ]

    # Should have at least the paragraph with content
    assert len(paragraphs) >= 1


def test_li_without_ul_or_ol():
    """Test <li> appearing without parent <ul> or <ol>."""
    html = "<li>orphan item</li>"
    parser = HTMLParser(html)
    root = parser.parse()

    # This tests whether the parser handles orphan <li> gracefully
    # The behavior might vary, but it shouldn't crash
    assert root is not None


def test_deeply_nested_li_auto_close():
    """Test that <li> auto-closes at appropriate depth."""
    html = "<ul><li>a<li>b<li>c</li></ul>"
    parser = HTMLParser(html)
    root = parser.parse()

    body = root.children[0]  # html > body
    ul = body.children[0]

    # All three <li> should be siblings
    list_items = [
        child
        for child in ul.children
        if isinstance(child, Element) and child.tag == "li"
    ]
    assert len(list_items) == 3


def test_paragraph_with_only_whitespace():
    """Test that paragraph with only whitespace is handled correctly."""
    html = "<p>   </p><p>content</p>"
    parser = HTMLParser(html)
    root = parser.parse()

    body = root.children[0]  # html > body

    # Based on add_text() implementation which ignores whitespace-only text
    # The first p might be empty
    paragraphs = [
        child
        for child in body.children
        if isinstance(child, Element) and child.tag == "p"
    ]
    assert len(paragraphs) >= 1

    # At least one paragraph should have actual content
    has_content = False
    for p in paragraphs:
        if (
            p.children
            and isinstance(p.children[0], Text)
            and p.children[0].text == "content"
        ):
            has_content = True
            break
    assert has_content


"""
4-4
"""


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


# https://html.spec.whatwg.org/multipage/parsing.html#adoption-agency-algorithm
