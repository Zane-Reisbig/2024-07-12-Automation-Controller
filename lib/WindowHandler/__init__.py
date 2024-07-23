# fmt: off
import os
from time import sleep
from win32con import (
    # Security Options
    PROCESS_QUERY_INFORMATION,
    PROCESS_VM_READ,

    # Process Options
    PM_NOREMOVE,

    # Window Messages
    SW_MINIMIZE,
    SW_MAXIMIZE,
    WM_CLOSE,
)
# fmt: on

HANDLE_ERROR_DESTRUCTIVE = 1
HANDLE_ERROR_STD_OUTPUT = 2

from typing import Callable, Any, Iterable, Mapping, TypeVar
from pywintypes import error as pywinError

T = TypeVar("T")
type WIN32_MESSAGE = int


class ThreadKill(Exception):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)


from dataclasses import dataclass, field, fields
from threading import Thread, Event

from win32api import OpenProcess, CloseHandle
from win32gui import (
    GetWindowText,
    GetForegroundWindow,
    EnumWindows,  # used in managers
    SetForegroundWindow,
    ShowWindow,
    SendMessage,
    PostMessage,
    GetWindowRect,
    SetWindowPos,
)
from win32process import (
    GetWindowThreadProcessId,
    AttachThreadInput,
    GetModuleFileNameEx,
)


class EventLoop(Thread):
    def __init__(
        self,
        tick: Callable[[], None],
        stopCheck: Callable[[], bool],
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.stopCheck = stopCheck
        self.tick = tick

        self.stopFlag = Event()
        self.isStopped = self.stopFlag.is_set

    def stop(self):
        if self.stopFlag.is_set():
            return

        self.stopFlag.set()
        self.join()

    def run(self):
        while self.stopFlag.is_set() == False and self.stopCheck() == False:
            self.tick()


class State:

    def __init__(
        self,
        inital=None,
        setHandler: Callable[[T, T], T] = None,
    ) -> None:
        """
        setHandler: function(curVal, prevVal) -> newValue

        ex: setHandler = lambda prev, set: return list([*prev, set])

        Now we have a State that will append instead of overwriting, for an accumulator
        """

        self.val = inital
        self.setHandler = setHandler

    def __eq__(self, value: object) -> bool:
        return self.val == value

    def hasVal(self):
        return self.val or None

    def setVal(self, to):
        if self.setHandler:
            self.val = self.setHandler(self.val, to)
            return

        self.val = to


@dataclass
class Point:
    x: int
    y: int


@dataclass
class Rect:
    # fmt: off
    left   : int = -1
    top    : int = -1
    right  : int = -1
    bottom : int = -1
    # fmt: on

    def toPoint(self):
        raise NotImplementedError("TODO")

    def __iter__(self):
        for field in fields(self):
            yield getattr(self, field.name)


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
    windowRect: Rect = field(default_factory=Rect)

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

        self.windowRect = Rect(*GetWindowRect(self.hwnd))

    def __eq__(self, value: object) -> bool:
        return (self.windowTitle, self.hwnd) == value

    # TODO: figure out why the hell the rect value is reseting
    def __set_window_to_original_pos__(self):
        w = self.windowRect.left - self.windowRect.right
        h = self.windowRect.bottom - self.windowRect.top
        SetWindowPos(
            self.hwnd,
            0,
            self.windowRect.left,
            self.windowRect.top,
            w,
            h,
            0,
        )

    def tryActivate(
        self,
        tryThreadAttach=True,
        # TODO: Flip this when rect resize issue is fixed
        withMinimize: bool = False,
        userVerify: Callable[["Window"], bool] = None,
        **kwargs,
    ):
        "kwarg: retryLimit"

        # TODO: Happens on return here
        foregroundWindow = getForegroundWindowAsObject()

        if tryThreadAttach:
            tryAttachThread(foregroundWindow.threadID, self.threadID)

        try:
            # By min and max-ing we make sure it truly is on the foreground
            if withMinimize:
                ShowWindow(self.hwnd, SW_MINIMIZE)  # 6 minimize
                ShowWindow(self.hwnd, SW_MAXIMIZE)  # 3 maximize
                self.__set_window_to_original_pos__()

            SetForegroundWindow(self.hwnd)
        except pywinError as e:
            # handle the failed to set foreground error
            __pywinIsError__(e, SetForegroundWindow)
            __pywinIsError__(e, ShowWindow)
            return False

        # Sometime it takes just a little longer than it should to raise the window
        # so we do this a little
        for _ in range(kwargs.get("retryLimit", 5)):
            if self.isForeground():
                break

        if userVerify != None:
            return userVerify(getForegroundWindowAsObject())

        # Unreachable code my ass, I'm stepped into it typing this
        return self.isForeground()

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
        return self.sendWindowMessage(WM_CLOSE, tryWaitForMessageToProcess=False)

    def sendWindowMessage(
        self,
        message: WIN32_MESSAGE,
        wParam: Any = None,
        lParam: Any = None,
        tryWaitForMessageToProcess: bool = True,
    ):
        isError = False

        if tryWaitForMessageToProcess:
            try:
                SendMessage(self.hwnd, message, wParam, lParam)

            except pywinError as e:
                __pywinIsError__(e, SendMessage)
                isError = True

            finally:
                return isError

        try:
            PostMessage(self.hwnd, message, wParam, lParam)

        except pywinError as e:
            __pywinIsError__(e, PostMessage)
            isError = True

        finally:
            return isError


def __pywinIsError__(
    _pywinError: pywinError, function: Callable, behavior: int = HANDLE_ERROR_STD_OUTPUT
):
    # Get the Literal Name of the callable and see if that's our error
    if _pywinError.funcname != function.__name__:
        if behavior == HANDLE_ERROR_DESTRUCTIVE:
            raise _pywinError
        elif behavior == HANDLE_ERROR_STD_OUTPUT:
            # A little non-destructive mode too
            print(_pywinError)
        else:
            raise NotImplementedError(f"Unknown option 'behavior={behavior}'")

    return


def getForegroundWindowAsObject():
    return getWindowAsObject(GetForegroundWindow())


def getWindowAsObject(hwnd: int, windowText: str = None):
    # GetWindowThreadProcessId returns the threadID and the processID
    #   so we just destructure it
    return Window(hwnd, *GetWindowThreadProcessId(hwnd), windowText)
    #                                                    ^
    #                                          if there is no windowText, oh well


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
