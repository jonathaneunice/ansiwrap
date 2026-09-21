from __future__ import annotations


class ANSIState:
    """
    Manage running state of a sequence of ANSI codes.
    """

    def __init__(
        self,
        fg: int | tuple[int, ...] | None = None,
        bg: int | tuple[int, ...] | None = None,
        style: list[int] | None = None,
    ) -> None:
        self.fg = fg
        self.bg = bg
        self.style = style
        self.seen: list[str] = []

    def consume(self, code: str) -> None:
        """
        Accept a code and update the current state to reflect its impact.
        """
        if code.startswith("\x1b["):
            code = code[2:]
        if code == "K":
            return
        if not code.endswith("m"):
            return

        vals = [int(v or 0) for v in code.rstrip("m").split(";")]
        while vals:
            top = vals.pop(0)
            if top == 0:
                self.fg = None
                self.bg = None
                self.style = None
            elif 1 <= top <= 9:
                if self.style is None:
                    self.style = []
                if top not in self.style:
                    self.style.append(top)
                self.style = sorted(self.style)
            elif 21 <= top <= 29:
                # Normal intensity clears both bold and faint (SGR 22).
                reset_styles = (1, 2) if top == 22 else (top - 20,)
                if self.style is not None:
                    self.style = [v for v in self.style if v not in reset_styles]
                if not self.style:
                    self.style = None
            elif 30 <= top < 38 or 90 <= top <= 97:
                # Standard (30–37) and bright/aixterm (90–97) foreground.
                self.fg = top
            elif top == 39:
                self.fg = None
            elif top == 38:
                under = vals.pop(0)
                if under == 5:
                    self.fg = (38, 5, vals.pop(0))
                elif under == 2:
                    self.fg = (38, 2, vals.pop(0), vals.pop(0), vals.pop(0))
                else:
                    raise ValueError("cant parse fg")
            elif 40 <= top < 48 or 100 <= top <= 107:
                # Standard (40–47) and bright/aixterm (100–107) background.
                self.bg = top
            elif top == 49:
                self.bg = None
            elif top == 48:
                under = vals.pop(0)
                if under == 5:
                    self.bg = (48, 5, vals.pop(0))
                elif under == 2:
                    self.bg = (48, 2, vals.pop(0), vals.pop(0), vals.pop(0))
                else:
                    raise ValueError("cant parse bg")
        if vals:
            raise ValueError(f"unconsumed SGR parameters: {vals}")
        self.seen.append(code)

    def code(self) -> str:
        """
        Return an ANSI code that creates the current state.
        """

        def codearr(c: int | tuple[int, ...] | list[int] | str | None) -> list[str]:
            if c is None:
                return []
            if isinstance(c, str):
                return [c]
            if isinstance(c, (tuple, list, set)):
                return [";".join(str(p) for p in c)]
            return [str(c)]

        raw_parts: list[str] = []
        raw_parts.extend(codearr(self.fg))
        raw_parts.extend(codearr(self.bg))
        raw_parts.extend(codearr(self.style))
        parts = [p for p in raw_parts if p is not None]
        if parts:
            return "\x1b[{}m".format(";".join(str(p) for p in parts))
        return ""

    def __repr__(self) -> str:
        clsname = self.__class__.__name__
        guts = "fg={fg}, bg={bg}, style={style}".format(**self.__dict__)
        return f"{clsname}({guts})"

    def __str__(self) -> str:
        dash = "\u2014"

        def nn(x: object) -> object:
            return dash if x is None else x

        return f"({nn(self.fg)}, {nn(self.bg)}, {nn(self.style)})"
