
from ansiwrap.textwrap import wrap
from ansiwrap import wrap as awrap

def test_real_emdash_wrap():
    """
    Base textwrap doesn't recognize real Unicode emdashes
    the way it recognizes the double-hyphen -- ASCII equivalent.
    But understanding of those was added to our copy, so test
    that one specific function.
    """
    text = u'this\u2014is'
    answer = [u'this\u2014', u'is']
    wrap_result = wrap(text, 6)
    awrap_result = awrap(text, 6)
    assert wrap_result == answer
    assert awrap_result == answer


def test_max_lines_extra():
    # Test a relatively rare case which seems to occur
    # when max_lines isn't sufficient to wrap thw whole
    # text, but the length of what would be the last
    # wrapped line is such that the placeholder cannot
    # be added without violence. So, add the placeholder
    # to the penultimate line.

    text = 'Rmya zyirv uhsjij blfsccwy tyt mr mq xwpx kija?\n\n'
    result = wrap(text, 12, max_lines=3, placeholder='*****')
    expect = ['Rmya zyirv', 'uhsjij*****']
    assert expect == result
