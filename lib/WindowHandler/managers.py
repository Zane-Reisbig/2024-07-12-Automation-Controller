from . import *

from threading import Thread
from time import sleep

QUICK_EVENT_TRY_MAX_ITERATIONS = 2
QUICK_EVENT_RETRY_TIME = 0.2

# EVENT_TRY_MAX_ITERATIONS: 1.38 hours if it ran all the way
EVENT_TRY_MAX_ITERATIONS = 9999
EVENT_RETRY_TIME = 0.5


def doesWindowExistIsItForeground(
    windowKeyword: str, ignore: list | str = None, trySetForegroundIfNot=True, **kwargs
):
    """
    kwargs:
        exact: bool
        withMinimize: bool = False
    """
    hasWindow, isForeground = False, False
    thisSearchForWindow = lambda: searchForWindowByTitle(
        windowKeyword, ignore, kwargs.get("exact", None)
    )

    doesWindowExist = thisSearchForWindow()
    if not doesWindowExist:
        return (hasWindow, isForeground)

    hasWindow = True

    if trySetForegroundIfNot and not doesWindowExist.isForeground():
        doesWindowExist.tryActivate(withMinimize=kwargs.get("withMinimize", True))

    isForeground = doesWindowExist.isForeground()

    return (hasWindow, isForeground)


def watchWindow(windowSearchArgs: list, time: int, maxIter: int):
    haveWindow = None

    for _ in range(maxIter):
        haveWindow = searchForWindowByTitle(*windowSearchArgs)

        if haveWindow:
            break

        sleep(time)

    return haveWindow


def event_foregroundWindowChanged(
    callback: Callable[[Window], None], timeout: int = 10
):
    curForeground = State(getForegroundWindowAsObject())

    def eventTick():
        newCurFore = getForegroundWindowAsObject()

        if newCurFore != curForeground.val:
            callback(newCurFore)
            return

        sleep(EVENT_RETRY_TIME)

    threadHandle = EventLoop(eventTick, timeoutSeconds=timeout)
    threadHandle.start()
    return threadHandle


def event_windowCreated(
    callback: Callable[[Window], None],
    windowSearchKwargs: dict,
    windowSearchArgs: list = [],
):
    haveWindow = State(None)

    def eventTick():
        haveWindow.setVal(
            searchForWindowByTitle(
                *windowSearchArgs,
                **windowSearchKwargs,
            )
        )
        if haveWindow.val != None:
            callback(haveWindow.val)
            return

        sleep(EVENT_RETRY_TIME)

    ret = EventLoop(eventTick, lambda: haveWindow.val != None)
    ret.start()
    return ret


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
    if keyword == "":
        return None

    # If the window text contains __EMPTY_STRING__ something crazy is going on and thats on you
    if not ignore:
        ignore = EmptyString

    if type(ignore) != list:
        ignore = [
            ignore,
        ]

    # Sometimes the kwargs don't get destructored I haven't been able to figure out why tho
    if type(keyword) == dict:
        keyword = keyword.get("keyword")

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
