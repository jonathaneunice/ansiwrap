
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

