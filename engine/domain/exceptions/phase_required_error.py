"""A deck was requested without naming the phase it sells."""

from __future__ import annotations

from engine.domain.exceptions.app_error import AppError


class PhaseRequiredError(AppError):
    """The project defines several phases and the request named none.

    A deck sells one phase, so on a multi-phase project the caller names it.
    """

    def __init__(self, defined: list[str]) -> None:
        self.defined = defined
        if defined:
            message = (
                "The slide deck is built for one phase: name it with 'phase' "
                f"(one of {', '.join(defined)})"
            )
        else:
            message = "The project defines no phases, so there is no deck to build"
        super().__init__(message)
