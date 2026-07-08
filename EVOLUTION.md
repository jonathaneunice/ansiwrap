# ansiwrap evolution notes

Working backlog from the 1.0 modernization review. This is an internal
planning doc, not user-facing documentation.

Related: `tests/TESTING.md` covers the testing strategy and remaining test
gaps. **Do not duplicate that material here**; link to it when a product
decision and a test decision are the same work item.

## Done in this pass

- **Legacy packaging purge** — Removed conflicting pre-hatchling artifacts
  that contradicted `pyproject.toml`:
  - `setup.py` (advertised 0.8.4, Python 2, `textwrap3`)
  - `.travis.yml` (replaced by `.github/workflows/ci.yml`)
  - `MANIFEST.in` (pointed at old `test/` layout)
  - `toxcov.ini` (old py27 / `textwrap3` coverage tox)
  - empty `README` (superseded by `README.rst`)
  - tracked `PKG-INFO` (stale 0.8.4 metadata)
- **`_textwrap` strategy comment** — Module docstring in
  `ansiwrap/_textwrap.py` records positives (zero deps, host fidelity /
  bug-compatibility with current `textwrap`) and tradeoffs (cross-version
  drift, `exec` auditability). Fuller user-facing docs still TODO below.

Single source of truth for packaging: `pyproject.toml` (hatchling) + GHA +
`tox.ini`.

---

## Product / API

### Align or document `shorten` vs unified `indent`

`wrap` / `fill` accept a unified `indent` kwarg via `_unified_indent`.
`shorten` builds `TextWrapper` directly and raises `TypeError` if `indent=`
is passed. Either:

- Route `shorten` through `_unified_indent`, or
- Document that `indent` is wrap/fill-only.

### Remove or use `_ansi_optimize`

Private helper only referenced from low-level tests, never from the public
wrap path. Either wire it in (e.g. strip redundant EL after wrap) or delete
it so the surface stays honest.

### Harden `ANSIState` for real CLI input

- ~~Bright FG/BG (90–97, 100–107) silently dropped from reopen codes~~ —
  fixed: `ANSIState`, render oracle, Hypothesis openers, low-level + golden
  wrap tests.
- Malformed / truncated 38/48 (256 / truecolor) sequences can `IndexError`
  instead of ignoring or partially applying.
- Prefer ignore/partial-parse over raising when wrapping untrusted output.
- `assert not vals` in `consume` disappears under `-O`; prefer an explicit
  check or drop it.

### Public vs private surface

- `ANSIState` is importable but not in `__all__`.
- Decide: document as supported, or treat as internal and keep confidence
  on public/behavioral tests (see also `tests/TESTING.md` on shrinking
  low-level field assertions).

### CSI / escape contract (product half of strip/corpus work)

Code only treats SGR (`…m`) and EL (`K`). OSC, clears, cursor moves, and
many other CSI forms are ignored or counted toward visible length.
Incomplete sequences (e.g. truncated `\x1b[31m…`) can break layout.

Decide and document: “well-formed SGR + EL only” vs a broader ignore list.
Strip/corpus test work in `tests/TESTING.md` should follow that contract.

### Mid-word CSI + `break_long_words`

Known limitation of len-monkey-patch + raw-index slicing. Fix or formally
scope in README; keep the xfail until then. Details and test plan:
`tests/TESTING.md`.

### Display width / Unicode

Measurement is code-point length, not terminal columns (CJK, emoji, etc.).
Future `wcwidth` (or equivalent) track is outlined in `tests/TESTING.md`;
user docs should state the current limitation until then.

---

## Documentation (user-facing)

README is clear on the core idea but should eventually cover:

1. Unified `indent` on `wrap` / `fill` (and `shorten` policy once decided).
2. Known limitations: mid-word CSI + `break_long_words`; width = code points
   not display columns.
3. Supported CSI surface (SGR + EL today).
4. Python 3.10+, zero runtime dependencies (for 0.8.x / `textwrap3` upgraders).
5. **`_textwrap` loading strategy** — expand the in-code comment into a short
   README or docs note: host `textwrap` fidelity and bug-compatibility as a
   feature; cross-version differences as expected. See
   `ansiwrap/_textwrap.py`.

Optional polish: richer `[project.urls]` (Changelog, Issues), LICENSE
copyright year, Development Status classifier if 1.0 means Stable.

---

## Packaging / tooling (remaining)

- Confirm nothing still references deleted `setup.py` / Travis / `MANIFEST.in`.
- Consider dropping `PYTHONPATH = {toxinidir}` in `tox.ini` once installs are
  clean without path munging (`usedevelop = False` today).
- Optional: ship `py.typed` for typed consumers (internal annotations already
  exist).

---

## Suggested priority

1. ~~Purge conflicting legacy packaging~~ (done).
2. Document contract + limitations in README (indent, CSI scope, mid-word
   break, Unicode width, 3.10+, `_textwrap` fidelity story).
3. Align `shorten` with `indent` (or document exclusion); remove or use
   `_ansi_optimize`.
4. Harden `ANSIState` further (malformed / truncated 38/48) if CLI corpora
   matter; bright SGR reopen is done.
5. Optional: `py.typed`, Stable classifier, copyright / project.urls polish.
6. Testing backlog items — track in `tests/TESTING.md`, not here.
