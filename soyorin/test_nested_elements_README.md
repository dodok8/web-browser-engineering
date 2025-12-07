# Test Suite for Nested Paragraphs and List Items Exercise

## Overview

This test suite verifies the implementation of the exercise that prevents nested `<p>` and `<li>` elements while still allowing nested lists.

## Exercise Requirements

1. **Nested Paragraphs**: Documents like `<p>hello<p>world</p>` should result in two sibling paragraphs instead of one paragraph inside another
2. **Nested List Items**: Similar behavior for `<li>` elements - they should auto-close when a new `<li>` is opened
3. **Nested Lists Still Allowed**: `<ul>` and `<ol>` elements should still be nestable inside `<li>` elements

## Test File

`test_nested_elements.py` - Contains 19 comprehensive test cases

## Running the Tests

```bash
# Using Python 3.12 (required for the lexer.py syntax)
python3.12 -m pytest soyorin/test_nested_elements.py -v

# Run specific test class
python3.12 -m pytest soyorin/test_nested_elements.py::TestNestedParagraphs -v

# Run specific test
python3.12 -m pytest soyorin/test_nested_elements.py::TestNestedParagraphs::test_simple_nested_paragraph -v
```

## Test Coverage

### 1. TestNestedParagraphs (5 tests)

Tests for preventing nested paragraph elements:

- `test_simple_nested_paragraph`: Verifies `<p>hello<p>world</p>` creates two sibling paragraphs
- `test_multiple_nested_paragraphs`: Tests multiple consecutive `<p>` tags
- `test_paragraph_with_other_elements`: Ensures `<p>` can still contain inline elements like `<em>`
- `test_paragraph_auto_close_on_opening`: Tests auto-closing when new `<p>` is opened
- `test_empty_nested_paragraph`: Tests `<p><p>content</p>` handling

### 2. TestNestedListItems (3 tests)

Tests for preventing nested list item elements:

- `test_simple_nested_li`: Verifies `<li>item1<li>item2</li>` creates two sibling list items
- `test_multiple_nested_li`: Tests multiple consecutive `<li>` tags
- `test_li_with_inline_elements`: Ensures `<li>` can still contain inline elements

### 3. TestNestedLists (3 tests)

Tests that nested lists are STILL ALLOWED:

- `test_nested_ul_inside_li`: Verifies `<ul>` can be nested inside `<li>`
- `test_nested_ol_inside_li`: Verifies `<ol>` can be nested inside `<li>`
- `test_multiple_levels_of_nesting`: Tests 3+ levels of list nesting

### 4. TestMixedScenarios (4 tests)

Tests combining paragraphs and lists:

- `test_paragraph_inside_li`: Tests `<li><p>text</p></li>`
- `test_list_between_paragraphs`: Tests paragraph-list-paragraph structure
- `test_nested_p_in_nested_li`: Tests that nested `<p>` still doesn't work inside `<li>`
- `test_complex_document_structure`: Tests a complex document with multiple elements

### 5. TestEdgeCases (4 tests)

Edge cases and special scenarios:

- `test_empty_paragraph_siblings`: Tests consecutive empty `<p>` tags
- `test_li_without_ul_or_ol`: Tests orphan `<li>` tags
- `test_deeply_nested_li_auto_close`: Tests `<li>` auto-closing behavior
- `test_paragraph_with_only_whitespace`: Tests whitespace-only paragraphs

## Current Status (Before Implementation)

```
17 failed, 2 passed
```

The 2 passing tests are:
- `test_empty_nested_paragraph` (passes by coincidence)
- `test_li_without_ul_or_ol` (just checks it doesn't crash)

## Implementation Guide

To make these tests pass, you need to modify the `implicit_tags()` method in `lexer.py` (lines 205-221) to:

1. **Detect when a `<p>` tag is opened while another `<p>` is open**
   - Check if "p" is already in the open_tags list
   - If yes, auto-close it by calling `self.add_tag("/p")`

2. **Detect when a `<li>` tag is opened while another `<li>` is open**
   - Check if "li" is already in open_tags
   - If yes, auto-close it by calling `self.add_tag("/li")`

3. **Still allow nested lists**
   - Do NOT auto-close `<li>` when `<ul>` or `<ol>` is opened
   - `<ul>` and `<ol>` should be allowed inside `<li>`

## Example Implementation Approach

```python
def implicit_tags(self, tag):
    while True:
        open_tags = [node.tag for node in self.unfinished]

        # Existing html/head/body logic...

        # Auto-close <p> when opening a new <p>
        if tag == "p" and "p" in open_tags:
            self.add_tag("/p")
            continue

        # Auto-close <li> when opening a new <li>
        if tag == "li" and "li" in open_tags:
            self.add_tag("/li")
            continue

        # ... rest of the logic
        else:
            break
```

## Success Criteria

All 19 tests should pass after implementation:
```
19 passed
```

## Notes

- Tests use tree navigation: `root.children[0]` → html, `root.children[0].children[0]` → body
- Tests check element types using `isinstance(elem, Element)` and `isinstance(elem, Text)`
- Tests verify tag names, children count, and text content
- Some tests are designed to be flexible about implementation details (e.g., whether empty elements are preserved)
