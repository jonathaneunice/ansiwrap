import pytest

from ansiwrap import ansi_terminate_lines, wrap


@pytest.mark.parametrize("intensity", ["1", "2", "1;2"])
def test_normal_intensity_is_not_reopened(intensity):
    first = f"\x1b[{intensity}mbold\x1b[22m plain"
    assert ansi_terminate_lines([first, "next"]) == [first, "next"]


def test_normal_intensity_preserves_other_attributes():
    first = "\x1b[31;1;2;3mbold\x1b[22m plain"
    assert ansi_terminate_lines([first, "next"]) == [
        first + "\x1b[0m",
        "\x1b[31;3mnext\x1b[0m",
    ]


def test_wrap_does_not_restore_reset_bold():
    assert wrap("\x1b[1mbold\x1b[22m plain next", width=10) == [
        "\x1b[1mbold\x1b[22m plain",
        "next",
    ]
