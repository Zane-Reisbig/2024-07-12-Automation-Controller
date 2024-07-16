from win32con import (
    PROCESS_QUERY_INFORMATION,
    PROCESS_VM_READ,
    SW_MINIMIZE,
    SW_MAXIMIZE,
    WM_CLOSE,
)

HANDLE_ERROR_DESTRUCTIVE = 0
HANDLE_ERROR_STD_OUTPUT = 1

from typing import Callable
from pywintypes import error as pywinError

from dataclasses import dataclass, field
from win32api import OpenProcess, CloseHandle
from win32gui import (
    GetWindowText,
    GetForegroundWindow,
    EnumWindows,
    SetForegroundWindow,
    ShowWindow,
    PostMessage,
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

    class HandleManager:
        def __init__(self, windowObject) -> None:
            self.windowObject = windowObject
            self.handle = None

        def __enter__(self):
            self.handle = OpenProcess(
                PROCESS_QUERY_INFORMATION | PROCESS_VM_READ,
                False,
                self.windowObject.processID,
            )

            return self.handle

        def __exit__(self, *args):
            CloseHandle(self.handle)

    def __post_init__(self):

        # Show me the difference between an HWND and and HANDLE and
        #   I'll let you know where the door is.
        #
        # Whoever decided they are different things is not welcome here
        with self.getHandle() as _handle:
            self.exePath = GetModuleFileNameEx(_handle, 0)
            CloseHandle(_handle)

        if self.windowTitle:
            return

        self.windowTitle = GetWindowText(self.hwnd)

        # If we set it to an EmptyString object, when we search our ignore
        #   list for the EmptyString and we can be sure it won't match
        if self.windowTitle == "":
            self.windowTitle = EmptyString

    def tryActivate(self, tryThreadAttach=True, withMinimize: bool = True) -> bool:
        foreGroundWindow = getForegroundWindowAsObject()
        if tryThreadAttach:
            tryAttachThread(foreGroundWindow.threadID, self.threadID)

        try:
            # By min and max-ing we make sure it truly is on the foreground
            if withMinimize:
                ShowWindow(self.hwnd, SW_MINIMIZE)  # 6 minimize
                ShowWindow(self.hwnd, SW_MAXIMIZE)  # 3 maximize

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

    def getHandle(self):
        """
        Returns a handle in a context manager for disposing

        ex: with window.getHandle() as handle:
                doUrStuffWith(handle)

        Disposes when outside of block
        """

        try:
            return self.HandleManager(self)
        except pywinError as e:
            __pywinIsError__(e, OpenProcess)

        return False

    def tryDestroy(self):
        try:
            PostMessage(self.hwnd, WM_CLOSE)
        except pywinError as e:
            __pywinIsError__(e, PostMessage)
            return False

        return True


def __pywinIsError__(_pywinError: pywinError, function: Callable, behavior: int = 0):
    # Get the Literal Name of the callable and see if that's our error
    if _pywinError.funcname != function.__name__:
        if behavior == HANDLE_ERROR_DESTRUCTIVE:
            raise _pywinError
        elif behavior == HANDLE_ERROR_STD_OUTPUT:
            # A little non-destructive mode too
            print(_pywinError)

    return


def getForegroundWindowAsObject():
    return getWindowAsObject(GetForegroundWindow())


def getWindowAsObject(hwnd: int, windowText: str = None):
    # GetWindowThreadProcessId returns the threadID and the processID
    #   so we just destructure it
    return Window(hwnd, *GetWindowThreadProcessId(hwnd), windowText)
    #                                                    ^
    #                                          if there is no windowText, oh well


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

    # If the thread is already the same it will throw an Exception
    if thisThread == willBeAttachedToThisThread:
        return True

    try:
        # No harm in handling it anyway, there is a chance the window will be
        #   raised anyway, but that's on you if it fails
        AttachThreadInput(thisThread, willBeAttachedToThisThread, True)

    except pywinError as e:
        __pywinIsError__(e, AttachThreadInput)
        return False

    return True
