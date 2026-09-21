import pytest

from ansiwrap import ansi_terminate_lines, ansilen, strip_color


@pytest.mark.parametrize("text", ["\x1b[2Jhello modern terminal", "\x1b[Aplain message"])
def test_unrecognized_sequence_does_not_consume_text(text):
    assert strip_color(text) == text
    assert ansilen(text) == len(text)
    assert ansi_terminate_lines([text]) == [text]


def test_unrecognized_sequence_before_real_color():
    text = "\x1b[2Jhello \x1b[31mred\x1b[0m"
    assert strip_color(text) == "\x1b[2Jhello red"
    assert ansi_terminate_lines([text]) == [text]
