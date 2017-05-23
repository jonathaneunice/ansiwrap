# Eventually would like to run the full tests for textwrap
# from the official Python repo
# https://github.com/python/cpython/blob/master/Lib/test/test_textwrap.py
# changing just the imports to bring in ansiwrap rather than
# textwrap.

# Until then, just a simple skip to remind us this needs to be done.

import pytest

@pytest.mark.skip(reason="test not implemented")
def test_dummy():
    with pytest.raises(Exception):
        raise RuntimeError('TBD')

