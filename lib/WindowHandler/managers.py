from . import *


def searchForWindowsByTitle(
    keyword: str, ignore: list | str = None, exact: bool = False
) -> list[Window]:
    # A working example of a list State
    listState = State(list(), setHandler=lambda cur, passed: list([*cur, passed]))
    #                                                                   ^
    #              Destructure what we have now, append the new value, return the new list

    return __EnumWindows__(
        listState,
        keyword,
        ignore,
        exact,
    )


def searchForWindowByTitle(
    keyword: str, ignore: list | str = None, exact: bool = False
) -> Window | None:
    singleState = State()

    return __EnumWindows__(singleState, keyword, ignore, exact, breakOnFirst=True)


def __EnumWindows__(
    accumulator: State,
    keyword: str,
    ignore: list | str = None,
    exact: bool = False,
    breakOnFirst: bool = False,
) -> Window | list[Window]:

    # If the window text contains __EMPTY_STRING__ something crazy is going on and thats on you
    if not ignore:
        ignore = EmptyString

    if type(ignore) != list:
        ignore = [
            ignore,
        ]

    exactComp = lambda this, that: this == that  #
    fuzzyComp = lambda this, that: this in that  # I was proud to come up with this
    useComp: Callable = exactComp if exact else fuzzyComp  #

    def enumProc(hwnd: int, accumulator: State):
        # I like this too
        if breakOnFirst and accumulator.hasVal():
            return

        winText = GetWindowText(hwnd)
        # Skip all blank windows, gotta go fast
        if winText == "":
            return

        if useComp(keyword, winText) and not any(
            [True for ig in ignore if str(ig) in winText]
        ):
            accumulator.setVal(getWindowAsObject(hwnd, windowText=winText))
            return

    EnumWindows(enumProc, accumulator)
    return accumulator.val  # Return the values we got from the State
