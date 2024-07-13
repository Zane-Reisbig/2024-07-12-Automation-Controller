from win32con import PROCESS_QUERY_INFORMATION, PROCESS_VM_READ
from typing import Callable
from pywintypes import error as pywinError

from dataclasses import dataclass, field
from win32api import OpenProcess
from win32gui import (
    GetWindowText,
    GetForegroundWindow,
    EnumWindows,
    SetForegroundWindow,
    ShowWindow,
)
from win32process import (
    GetWindowThreadProcessId,
    AttachThreadInput,
    GetModuleFileNameEx,
)


class State:
    def __init__(
        self,
        inital=None,
        setHandler: Callable = None,
    ) -> None:
        """
        setHandler: function(curVal, prevVal) -> newValue

        ex: setHandler = lambda prev, set: return list([*prev, set])

        Now we have a State that will append instead of overwriting, for an accumulator
        """

        self.val = inital
        self.setHandler = setHandler

    def hasVal(self):
        return None != self.val

    def setVal(self, to):
        if self.setHandler:
            self.val = self.setHandler(self.val, to)
            return

        self.val = to


# I like C#'s String.Empty class member a lot
class EmptyString(str):
    def __str__(self) -> str:
        return "__EMPTY_STRING__"


@dataclass
class Window:
    hwnd: int
    threadID: int
    processID: int
    windowTitle: str = field(default_factory=str)
    exePath: str = field(default_factory=str)

    def __post_init__(self):

        # Show me the difference between an HWND and and HANDLE and
        #   I'll let you know where the door is.
        #
        # Whoever decided they are different things is not welcome here
        self.exePath = GetModuleFileNameEx(
            OpenProcess(
                PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, self.processID
            ),
            0,
        )

        if self.windowTitle:
            return

        self.windowTitle = GetWindowText(self.hwnd)

        # If we set it to an EmptyString object, when we search our ignore
        #   list for the EmptyString and we can be sure it won't match
        if self.windowTitle == "":
            self.windowTitle = EmptyString

    def tryActivate(self, tryThreadAttach=True) -> bool:
        foreGroundWindow = getForegroundWindowAsObject()
        if tryThreadAttach:
            tryAttachThread(foreGroundWindow.threadID, self.threadID)

        try:
            # By min and max-ing we make sure it truly is on the foreground
            ShowWindow(self.hwnd, 6)  # 6 minimize
            ShowWindow(self.hwnd, 3)  # 3 maximize
            SetForegroundWindow(self.hwnd)
        except pywinError as e:
            # handle the failed to set foreground error
            __pywinIsError__(e, SetForegroundWindow)
            __pywinIsError__(e, ShowWindow)
            return False

        return True

    def isForeground(self):
        foreGround = getForegroundWindowAsObject()

        if foreGround.hwnd == self.hwnd or foreGround.windowTitle == self.windowTitle:
            return True

        return False


def __pywinIsError__(_pywinError: pywinError, function: Callable, behavior: int = 0):

    # Get the Literal Name of the callable and see if that's our error
    if _pywinError.funcname != function.__name__:
        if behavior == 0:
            raise _pywinError
        elif behavior == 1:
            # A little non-destructive mode too
            print(_pywinError)

    return


def getForegroundWindowAsObject():
    return getWindowAsObject(GetForegroundWindow())


def getWindowAsObject(hwnd: int, **kwargs):
    # GetWindowThreadProcessId returns the threadID and the processID
    #   so we just destructure it
    return Window(hwnd, *GetWindowThreadProcessId(hwnd), kwargs.get("windowText"))
    #                                                    ^
    #                                            if there is no windowText oh well


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


def tryAttachThread(thisThread: int, willBeAttachedToThisThread: int):
    # fmt: off
    assert type(thisThread) == int                 , f"{thisThread} is not type 'int'"
    assert type(willBeAttachedToThisThread) == int , f"{willBeAttachedToThisThread} is not type 'int'"
    # fmt: on

    # If the thread is already the same it will throw and Exception
    if thisThread == willBeAttachedToThisThread:
        return True

    try:
        # No harm in handling it anyway, there is a change the window will be
        #   raised anyway, but that's on you if it fails
        AttachThreadInput(thisThread, willBeAttachedToThisThread, True)

    except pywinError as e:
        __pywinIsError__(e, AttachThreadInput, behavior=1)
        return False

    return True
