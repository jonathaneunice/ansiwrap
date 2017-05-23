
from __future__ import print_function
from ansiwrap import *
import textwrap
from colors import *
import sys

try:
    ascii
except NameError:  # Python 2
    ascii = repr

text = (red('This') + ' is ' + color('some', fg=11, bg=55, style='bold') +
       blue(' very nice') + ' ' + yellow('colored') +
       ' text ' + green('that is hard to') + yellow(' nicely ')
       + green('wrap because') +
       red(' of the ') + blue('ANSI', bg='yellow') + yellow(' codes.') +
       red(' But') + blue(' ansiwrap ') + green('does fine.'))


text = ('textwrap\ndoes\nplain\ntext\nwell.\n' + red('But') + ' text ' +
       color('colored', fg=11, bg=55, style='bold') +
       yellow(' with ') + red('embedded ') + blue('ANSI', bg='yellow') +
       green(' codes') + yellow('?')
       + green(' Not') +
       red(' so ') + blue('good ') + magenta('there') + cyan('.'))
       # + color(' ansiwrap ', style='italic') + 
       # yellow('has') + red(' no') + green(' such ') + blue('limits.'))


print(ascii(text))

width = 30
ruler = '----+----|' * 3

print("All one line:")
print(text)
print()


print(ruler)
print(textwrap.fill(text, width))

print(ruler)
print(fill(text, width))

print(ruler)
print(textwrap.fill(strip_color(text), width))

print(ruler)
print()
print("ansiwrap output should look identical to")
print("textwrap output...with the exception of color.")
print()

from say import say

say(fill(text, width), prefix='| ')
