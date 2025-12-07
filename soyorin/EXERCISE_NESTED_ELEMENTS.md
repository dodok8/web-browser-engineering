# Exercise: Preventing Nested Paragraphs and List Items

## Problem Statement

It's not clear what it would mean for one paragraph to contain another. Change the parser so that a document like `<p>hello<p>world</p>` results in two sibling paragraphs instead of one paragraph inside another; real browsers do this too. Do the same for `<li>` elements, but make sure nested lists are still possible.

## Test Suite

Created: `test_nested_elements.py`
Documentation: `test_nested_elements_README.md`

### Quick Start

```bash
# Run all tests for this exercise
python3.12 -m pytest soyorin/test_nested_elements.py -v

# Expected before implementation: 17 failed, 2 passed
# Expected after implementation: 19 passed
```

## Test Examples

### Example 1: Nested Paragraphs
```html
Input:  <p>hello<p>world</p>
Output: Two sibling <p> elements, not nested
```

**Expected Structure:**
```
body
├── p
│   └── Text("hello")
└── p
    └── Text("world")
```

### Example 2: Nested List Items
```html
Input:  <ul><li>item1<li>item2</li></ul>
Output: Two sibling <li> elements
```

**Expected Structure:**
```
ul
├── li
│   └── Text("item1")
└── li
    └── Text("item2")
```

### Example 3: Nested Lists (Should Still Work!)
```html
Input:  <ul><li>parent<ul><li>child</li></ul></li></ul>
Output: Nested list structure preserved
```

**Expected Structure:**
```
ul
└── li
    ├── Text("parent")
    └── ul
        └── li
            └── Text("child")
```

## Implementation Hints

### Location
Modify the `implicit_tags()` method in `lexer.py` (lines 205-221)

### Key Logic

1. **Auto-close `<p>` when opening new `<p>`:**
   ```python
   if tag == "p" and "p" in open_tags:
       self.add_tag("/p")
       continue
   ```

2. **Auto-close `<li>` when opening new `<li>`:**
   ```python
   if tag == "li" and "li" in open_tags:
       self.add_tag("/li")
       continue
   ```

3. **Important:** Don't auto-close `<li>` when `<ul>` or `<ol>` is opened!
   - Nested lists must still be allowed
   - Only close `<li>` when another `<li>` is encountered

### Testing Your Implementation

```bash
# Run tests and see progress
python3.12 -m pytest soyorin/test_nested_elements.py -v

# Run specific test categories
python3.12 -m pytest soyorin/test_nested_elements.py::TestNestedParagraphs -v
python3.12 -m pytest soyorin/test_nested_elements.py::TestNestedListItems -v
python3.12 -m pytest soyorin/test_nested_elements.py::TestNestedLists -v

# Run a single test
python3.12 -m pytest soyorin/test_nested_elements.py::TestNestedParagraphs::test_simple_nested_paragraph -v
```

## Test Coverage Summary

| Category | Tests | Description |
|----------|-------|-------------|
| **Nested Paragraphs** | 5 | Verify `<p>` tags auto-close when new `<p>` opens |
| **Nested List Items** | 3 | Verify `<li>` tags auto-close when new `<li>` opens |
| **Nested Lists** | 3 | Verify `<ul>`/`<ol>` can still nest inside `<li>` |
| **Mixed Scenarios** | 4 | Test combinations of paragraphs and lists |
| **Edge Cases** | 4 | Test unusual or boundary conditions |
| **TOTAL** | **19** | Comprehensive coverage |

## Success Criteria

✅ All 19 tests pass
✅ `<p>hello<p>world</p>` creates sibling paragraphs
✅ `<li>item1<li>item2</li>` creates sibling list items
✅ Nested lists like `<ul><li>parent<ul><li>child</li></ul></li></ul>` still work

## Browser Behavior Reference

Real browsers implement this same behavior:

```javascript
// In a real browser console:
document.body.innerHTML = '<p>hello<p>world</p>';
console.log(document.body.children.length); // 2 (not 1)
console.log(document.body.children[0].textContent); // "hello"
console.log(document.body.children[1].textContent); // "world"
```

This is defined in the HTML5 specification for "adoption agency algorithm" and auto-closing rules.
