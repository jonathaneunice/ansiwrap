"""
Demonstrate ansiwrap wrapping of ANSI-colored text.
"""

from colors import blue, color, cyan, green, magenta, red, yellow

from ansiwrap import fill, strip_color

text = (
    "textwrap\ndoes\nplain\ntext\nwell.\n"
    + red("But")
    + " text "
    + color("colored", fg=11, bg=55, style="bold")
    + yellow(" with ")
    + red("embedded ")
    + blue("ANSI", bg="yellow")
    + green(" codes")
    + yellow("?")
    + green(" Not")
    + red(" so ")
    + blue("good ")
    + magenta("there")
    + cyan(".")
)

width = 30
ruler = "----+----|" * 3

print("All one line:")
print(text)
print()
print(ruler)
print(fill(text, width))
print(ruler)
print(fill(strip_color(text), width))
print(ruler)
