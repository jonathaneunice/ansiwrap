# ansiwrap testing analysis

This document records the testing review done for ansiwrap, what was added
in the content-level / property-based pass, and what remains useful to do
later. It is a design and status note, not a user-facing README.

## Background: what the library must get right

ansiwrap mirrors `textwrap.wrap` / `fill` / `shorten`, but:

1. **Layout** — CSI sequences (colors, styles, erase-line) must not count
   toward wrap width.
2. **Style continuity** — when a wrap breaks inside a styled span, each
   physical line should reset at the end and reopen the active style at the
   start of the next line (`ansi_terminate_lines` + `ANSIState`).

A suite that only checks (1) can pass while (2) is wrong. Historically most
tests compared `strip_color(ansiwrap(...))` to `textwrap(...)` on the plain
string. That is necessary but not sufficient.

## Analysis of the prior suite

### What was already strong

| Area | Role |
|------|------|
| `same_behavior` + `test_one` / `test_two` | Human-shaped colored prose vs textwrap layout |
| `test_unified_indent` | Unified `indent` vs textwrap indent kwargs |
| `test_odd_states` | Less common CSI (EL, truecolor, terse reset) — still layout-only |
| Golden cases (`test_unterminated`, `test_known_text`, `test_doc_example`, shorten cases) | Exact byte outputs, human-verified |

These are valuable regression anchors. They should stay.

### What was weak or risky

1. **Heavy `ANSIState` unit tests** — Asserted internal fields (`fg` as int
   vs tuple, style list sorting, `repr`/`str`, `code()` spelling). That
   locks representation, not user-visible wrap/fill behavior. Useful for
   parser regressions, poor as the main confidence story.
2. **No style oracle** — Nothing checked that colors survive wrap breaks
   correctly except a few exact golden strings.
3. **Narrow input space** — A handful of hand-built strings and a mostly
   fixed width list (plus a little `random.sample` on widths).
4. **Private API tests mixed with public ones** — `_ansi_optimize` and
   `ANSIState` lived beside behavioral tests, blurring what is contract vs
   implementation.

### Known product limitation (surfaced by new tests)

`textwrap`’s `break_long_words` path slices by **raw string index**. When
CSI sits inside a word (or a colored word is longer than `width`), visible
layout can diverge from `textwrap` on the stripped string. ansiwrap’s
`len` monkey-patch fixes *measurement* of whole chunks, not *where*
`break_long_words` cuts.

This is documented as a strict xfail:
`test_known_limitation_midword_csi_break_long_words`.

A related gap: display width is Python `len()` after strip (every code
point counts as 1). East Asian wide characters, emoji, and combining marks
are out of scope until a wcwidth-aware path exists.

## What we added

### File layout

```text
tests/
  __init__.py                 # package marker for helper imports
  render_oracle.py            # independent SGR renderer (normalized Style)
  test_ansiwrap.py            # original behavioral + golden tests (unchanged in substance)
  test_ansistate_lowlevel.py  # isolated ANSIState / _ansi_optimize tests
  test_properties.py          # Hypothesis layout + style properties
  TESTING.md                  # this document
```

Low-level `ANSIState` tests were **moved, not removed**, and marked in the
module docstring as candidates for later deletion once content-level
coverage has proven itself.

### Render oracle (`render_oracle.py`)

An SGR interpreter independent of `ANSIState` that yields
`(visible_char, Style)` pairs. Styles are normalized (`fg`/`bg` tuples,
`attrs` as a frozenset) so tests compare **rendered appearance**, not CSI
byte spelling (`\x1b[31;1m` vs `\x1b[1;31m`).

Also provides `final_style`, `content_chars`, and `strip_csi`.

### Property tests (`test_properties.py`)

Hypothesis generators build colored prose with CSI at **word boundaries**
(styles may span multiple words / stay unterminated). Properties:

| Property | Checks |
|----------|--------|
| Layout vs `textwrap.wrap` / `fill` | Stripped lines and `ansilen` |
| Layout with unified indents | vs textwrap `initial_indent` / `subsequent_indent` |
| Rendered content styles after wrap | Non-whitespace `(char, Style)` stream |
| Trailing reset when a line ends mid-style | `final_style(line)` is default |
| `shorten` prefix styles | Kept content matches source style prefix |

Generators `assume` away overlong words so tests do not trip the
`break_long_words` limitation on every run; that case is pinned separately
as xfail.

### Dependencies

- `hypothesis` added to `[project.optional-dependencies] test` and `tox.ini`.

### Docstrings

All functions/methods under `tests/` use a consistent multi-line docstring
shape (summary line, blank line, body), including helpers and tests.

## What remains / could improve overall testing

Rough priority order:

### 1. Fix or formally scope the mid-word / long-word CSI bug

Either:

- Implement CSI-aware `break_long_words` (or disable breaking inside CSI and
  document the policy), then flip the xfail to a real test; or
- Document as a known limitation in the README and keep the xfail as the
  contract.

Until then, property generators correctly avoid that region.

### 2. Real-world corpus (deferred on purpose in the first pass)

Capture CLI output (`pytest`, `rich`, `git`, `ls --color`, build tools) and
store under something like `tests/corpus/`. Assert layout + rendered styles,
not exact CSI bytes. Highest realism per fixture; needs light curation.

External lists such as chalk’s `ansi-regex` fixtures are better for
**strip/match** coverage than for wrap semantics.

### 3. Harden `strip_color` / `ANSIRE` against a broader CSI set

Property tests focus on SGR (+ EL). A fixture-driven strip suite (common
CSI, OSC hyperlinks if ever relevant, malformed sequences) would clarify
what ansiwrap promises to ignore vs preserve.

### 4. Retire or shrink `test_ansistate_lowlevel.py`

Once property + corpus coverage is trusted:

- Keep at most “invalid 38/48 raises” *or* express that only via public API
  behavior.
- Drop `repr`/`str` and internal field-shape assertions unless `ANSIState`
  is documented as a public API.

### 5. Display-width / Unicode (explicit future work)

Comment and oracle docs already note width-1-only. A later track:

- Integrate `wcwidth` (or equivalent) for measurement.
- Add generators for CJK / emoji with clear expected column widths.
- Do not enable those generators until the library measures width correctly.

### 6. `shorten` edge cases

Current properties cover prefix styles with a fixed `"..."` placeholder.
Still thin on:

- Colored / multi-code-point placeholders
- `max_lines`-style interactions if exposed
- Exact interaction with indent kwargs

### 7. Visual / snapshot lane (optional, local)

A small script that prints corpus cases in a real terminal helps humans
verify reopen/reset. Keep CI on properties + goldens; do not require a TTY
in CI.

### 8. Determinism of legacy width sampling

`test_ansiwrap.py` still extends `LINE_LENGTHS` with `random.sample` each
run. Fine historically; for flake hunting, seed or replace with a fixed
extended set. New property tests already randomize widths aggressively via
Hypothesis.

### 9. Cross-check against peers (optional)

Libraries such as `wcwidth`’s sequence-aware wrap, or other ANSI-aware
wrappers, can provide second opinions on hard cases—not as a hard
dependency, but as occasional differential tests.

## Guiding principles going forward

1. Prefer **public API** and **rendered equality** over internal
   `ANSIState` field checks.
2. Use **textwrap as the layout oracle** and the **render oracle for
   style**.
3. Keep a **small set of human goldens**; grow breadth with generators and
   corpora, not more exact CSI strings.
4. Treat mid-word CSI + `break_long_words` and wide Unicode as **named
   gaps**, not silent assumptions.
5. Leave existing behavioral tests intact when adding new layers; isolate
   or deprecate low-level tests rather than rewriting history in place.

## Current status (at time of writing)

- Behavioral/golden suite preserved in `test_ansiwrap.py`.
- Low-level `ANSIState` tests isolated in `test_ansistate_lowlevel.py`.
- Hypothesis layout + style properties in `test_properties.py`.
- Suite: existing tests + new properties green; one strict xfail for the
  mid-word CSI / `break_long_words` limitation.
