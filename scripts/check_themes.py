#!/usr/bin/env python3
"""Check every theme in themes/: it sets every colour key YACE's default
theme sets, and its text meets the contrast rules the theme promises.

Usage: scripts/check_themes.py [THEMES_DIR]   (exit 1 on any failure)

Contrast is the WCAG 2 ratio: 4.5:1 is "AA" for text, 7:1 is "AAA".
"""
import pathlib, sys, tomllib

# The keys YACE's default theme (yace-dark) sets; a theme here sets all of
# them, so nothing falls back to another theme's colours.
COLORS = """editor.background editor.foreground descriptionForeground sideBar.background sideBar.foreground sideBarTitle.foreground tab.activeBackground tab.activeForeground tab.inactiveBackground tab.inactiveForeground editorGroupHeader.tabsBackground editorGroup.border focusBorder editor.selectionBackground editor.inactiveSelectionBackground editor.lineHighlightBackground editorLineNumber.foreground editorLineNumber.activeForeground editorCursor.background editorCursor.foreground editorBracketMatch.background statusBar.background statusBar.foreground statusBar.noFolderBackground list.activeSelectionBackground list.activeSelectionForeground list.inactiveSelectionBackground list.highlightForeground editorWidget.background editorWidget.foreground editorWidget.border quickInputList.focusBackground input.background editorError.foreground editorWarning.foreground editorInfo.foreground gitDecoration.modifiedResourceForeground gitDecoration.addedResourceForeground gitDecoration.deletedResourceForeground yace.dirtyForeground yace.missingRootForeground scrollbarSlider.background editorWhitespace.foreground editor.findMatchHighlightBackground editor.findMatchBackground editorSuggestWidget.highlightForeground terminal.background terminal.foreground terminal.ansiBlack terminal.ansiRed terminal.ansiGreen terminal.ansiYellow terminal.ansiBlue terminal.ansiMagenta terminal.ansiCyan terminal.ansiWhite terminal.ansiBrightBlack terminal.ansiBrightRed terminal.ansiBrightGreen terminal.ansiBrightYellow terminal.ansiBrightBlue terminal.ansiBrightMagenta terminal.ansiBrightCyan terminal.ansiBrightWhite""".split()
SYNTAX = """none comment string string.special string.escape character number boolean constant constant.builtin keyword keyword.control operator punctuation punctuation.bracket function function.builtin function.method function.macro type type.builtin constructor variable variable.builtin variable.parameter property attribute tag namespace label markup.heading markup.bold markup.italic markup.link markup.raw markup.list embedded""".split()

# What each theme promises: the minimum ratio for text, an optional maximum
# (Low Contrast stays soft), and the minimum for comments.
RULES = {
    "retro-blue": {"text": 4.5, "comment": 4.5},
    "phosphor": {"text": 4.5, "comment": 3.0},
    "high-contrast": {"text": 7.0, "comment": 7.0},
    "low-contrast": {"text": 4.5, "max": 7.0, "comment": 3.0},
}

# Text drawn on a background: (foreground key, background key).
UI_PAIRS = [
    ("editor.foreground", "editor.background"),
    ("editor.foreground", "editor.lineHighlightBackground"),
    ("editorLineNumber.activeForeground", "editor.background"),
    ("sideBar.foreground", "sideBar.background"),
    ("sideBarTitle.foreground", "sideBar.background"),
    ("tab.activeForeground", "tab.activeBackground"),
    ("tab.inactiveForeground", "tab.inactiveBackground"),
    # The active terminal tab is drawn on the terminal's background.
    ("tab.activeForeground", "terminal.background"),
    ("statusBar.foreground", "statusBar.background"),
    ("list.activeSelectionForeground", "list.activeSelectionBackground"),
    ("list.activeSelectionForeground", "quickInputList.focusBackground"),
    ("editorWidget.foreground", "editorWidget.background"),
    ("editorWidget.foreground", "input.background"),
    ("list.highlightForeground", "editorWidget.background"),
    ("terminal.foreground", "terminal.background"),
    ("editorError.foreground", "editor.background"),
    ("editorWarning.foreground", "editor.background"),
    ("editorInfo.foreground", "editor.background"),
    ("gitDecoration.modifiedResourceForeground", "sideBar.background"),
    ("gitDecoration.addedResourceForeground", "sideBar.background"),
    ("gitDecoration.deletedResourceForeground", "sideBar.background"),
]


def rgb(hex_):
    h = hex_.lstrip("#")
    assert len(h) == 6, f"{hex_}: use #rrggbb (no alpha) so contrast can be checked"
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def luminance(hex_):
    c = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb(hex_)]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def fg(v):
    return v if isinstance(v, str) else v["fg"]


def check(path):
    slug = path.stem
    t = tomllib.loads(path.read_text())
    problems = []
    colors, syntax = t.get("colors", {}), t.get("syntax", {})
    problems += [f"missing colour {k}" for k in COLORS if k not in colors]
    problems += [f"missing syntax {k}" for k in SYNTAX if k not in syntax]
    if slug not in RULES:
        return problems + [f"no contrast rule for {slug} in RULES"]
    if problems:
        return problems
    r = RULES[slug]

    def need(label, a, b, lo, hi=None):
        x = ratio(a, b)
        if x < lo - 1e-9 or (hi is not None and x > hi + 1e-9):
            want = f"{lo}:1" + (f" to {hi}:1" if hi else "")
            problems.append(f"{label}: {a} on {b} is {x:.2f}:1, needs {want}")

    for f_, b_ in UI_PAIRS:
        need(f"{f_} on {b_}", colors[f_], colors[b_], r["text"])
    need("editor text (max)", colors["editor.foreground"], colors["editor.background"], 0, r.get("max"))
    # Program output in the terminal stays readable (black excepted: it's
    # meant to match the background).
    for n in ["Red", "Green", "Yellow", "Blue", "Magenta", "Cyan", "White"]:
        for k in (f"terminal.ansi{n}", f"terminal.ansiBright{n}"):
            need(k, colors[k], colors["terminal.background"], 3.0)
    for k in SYNTAX:
        lo = r["comment"] if k == "comment" else r["text"]
        need(f"syntax {k}", fg(syntax[k]), colors["editor.background"], lo, None if k == "comment" else r.get("max"))
        # Selected code stays readable.
        need(f"syntax {k} on selection", fg(syntax[k]), colors["editor.selectionBackground"], min(lo, 3.0))
    return problems


def main():
    d = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).parent.parent / "themes")
    failed = False
    for path in sorted(d.glob("*.toml")):
        problems = check(path)
        t = tomllib.loads(path.read_text())
        c = t.get("colors", {})
        if "editor.foreground" in c and "editor.background" in c:
            print(f"{path.stem}: editor text {ratio(c['editor.foreground'], c['editor.background']):.1f}:1")
        for p in problems:
            print(f"  FAIL {p}")
        failed |= bool(problems)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
