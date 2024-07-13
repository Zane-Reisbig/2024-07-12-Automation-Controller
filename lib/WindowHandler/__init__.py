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


class EmptyString(str):
    def __str__(self) -> str:
        return "__EMPTY_STRING__"


@dataclass
class Window:
    hwnd: int
    threadID: int
    processID: int
    windowTitle: str = field(default_factory=str)
    exe: str = field(default_factory=str)

    def __post_init__(self):
        self.exe = GetModuleFileNameEx(
            OpenProcess(
                PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, self.processID
            ),
            0,
        )

        if self.windowTitle:
            return

        self.windowTitle = GetWindowText(self.hwnd)

        if self.windowTitle == "":
            self.windowTitle = EmptyString

    def tryActivate(self, tryThreadAttach=True) -> bool:
        foreGroundWindow = getForegroundWindowAsObject()
        if tryThreadAttach:
            tryAttachThread(foreGroundWindow.threadID, self.threadID)

        try:
            ShowWindow(self.hwnd, 6)  # 6 minimize
            ShowWindow(self.hwnd, 3)  # 3 maximize
            SetForegroundWindow(self.hwnd)
        except pywinError as e:
            raise e

        return True

    def isForeground(self):
        foreGround = getForegroundWindowAsObject()

        if foreGround.hwnd == self.hwnd or foreGround.windowTitle == self.windowTitle:
            return True

        return False


def __pywinIsError__(_pywinError: pywinError, code: Callable, behavior: int = 0):

    if _pywinError.funcname != code.__name__:
        if behavior == 0:
            raise _pywinError
        elif behavior == 1:
            print(_pywinError)

    return


def getForegroundWindowAsObject():
    return getWindowAsObject(GetForegroundWindow())


def getWindowAsObject(hwnd: int, **kwargs):
    return Window(hwnd, *GetWindowThreadProcessId(hwnd), kwargs.get("windowText"))


def searchForWindowsByTitle(
    keyword: str, ignore: list | str = None, exact: bool = False
) -> list[Window]:
    listState = State(list(), setHandler=lambda cur, passed: list([*cur, passed]))

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

    if not ignore:
        ignore = EmptyString

    if type(ignore) != list:
        ignore = [
            ignore,
        ]

    exactComp = lambda this, that: this == that
    fuzzyComp = lambda this, that: this in that
    useComp: Callable = exactComp if exact else fuzzyComp

    def enumProc(hwnd: int, accumulator: State):
        if breakOnFirst and accumulator.hasVal():
            return

        winText = GetWindowText(hwnd)
        if winText == "":
            return

        if useComp(keyword, winText) and not any(
            [True for ig in ignore if str(ig) in winText]
        ):
            accumulator.setVal(getWindowAsObject(hwnd, windowText=winText))
            return

    EnumWindows(enumProc, accumulator)
    return accumulator.val


def tryAttachThread(thisThread: int, willBeAttachedToThisThread: int):
    # fmt: off
    assert type(thisThread) == int                 , f"{thisThread} is not type 'int'"
    assert type(willBeAttachedToThisThread) == int , f"{willBeAttachedToThisThread} is not type 'int'"
    # fmt: on

    if thisThread == willBeAttachedToThisThread:
        return True

    try:
        AttachThreadInput(thisThread, willBeAttachedToThisThread, True)

    except pywinError as e:
        __pywinIsError__(e, AttachThreadInput, behavior=1)
        return False

    return True
