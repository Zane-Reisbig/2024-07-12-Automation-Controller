import os
import time
import unittest
import tkinter as tk

from win32con import WM_SETTEXT

from threading import Thread, Event

from uuid import uuid1
from lib.WindowHandler import Window
from lib.WindowHandler.managers import (
    event_windowCreated,
    searchForWindowByTitle,
    getForegroundWindowAsObject,
    doesWindowExistIsItForeground,
    Rect,
    State,
    pywinError,
)

# fmt: off
doAll = True
run_T_WindowHandlers = doAll if doAll else False
run_T_WindowMessage  = doAll if doAll else False
run_T_WindowManager  = doAll if doAll else False
run_T_WindowPosition = doAll if doAll else False
run_T_EventsTest     = doAll if doAll else False
# fmt: on

actionWaitTime = 0.2
windowCreateDestroyTime = 0.4


def createAndGetWindowRef(title: str, message: str = None):
    ready = Event()

    def createWindow():
        root = tk.Tk()
        root.title(title)
        label = tk.Label(root, text=message, anchor="center")
        label.pack()
        ready.set()
        root.mainloop()

    Thread(target=createWindow).start()
    ready.wait()
    time.sleep(windowCreateDestroyTime)

    return searchForWindowByTitle(title)


@unittest.skipIf(not run_T_WindowHandlers, "Not Testing")
class T_WindowHandlers(unittest.TestCase):

    def test_canCloseWindow(self):
        windowTitle = "Test Window"
        windowRef = createAndGetWindowRef(windowTitle)
        time.sleep(windowCreateDestroyTime)

        self.assertIsNotNone(windowRef)
        self.assertEqual(
            windowTitle,
            windowRef.windowTitle,
            f"\t- {windowTitle} != {windowRef.windowTitle}\n",
        )

        windowRef.tryDestroy()
        time.sleep(windowCreateDestroyTime)

        windowRef = searchForWindowByTitle(windowTitle)
        self.assertIsNone(windowRef)

    def test_canGetWindowReference(self):
        windowTitle = "Get this Window Ref"
        windowRef = createAndGetWindowRef(windowTitle)
        time.sleep(windowCreateDestroyTime)

        self.assertIsNotNone(windowRef)
        self.assertEqual(
            windowTitle,
            windowRef.windowTitle,
            f"\t- {windowTitle} != {windowRef.windowTitle}\n",
        )

        windowRef.tryDestroy()
        time.sleep(windowCreateDestroyTime)

    def test_canSwitchWindow(self):
        firstWindowTitle = "First"
        firstWindow = createAndGetWindowRef(firstWindowTitle)
        time.sleep(windowCreateDestroyTime)

        secondWindowTitle = "Second"
        secondWindow = createAndGetWindowRef(secondWindowTitle)
        time.sleep(windowCreateDestroyTime)

        firstWindow.tryActivate()
        self.assertEqual(getForegroundWindowAsObject().windowTitle, firstWindowTitle)

        time.sleep(actionWaitTime)

        secondWindow.tryActivate()
        self.assertEqual(getForegroundWindowAsObject().windowTitle, secondWindowTitle)

        time.sleep(actionWaitTime)

        firstWindow.tryDestroy()
        time.sleep(actionWaitTime)

        secondWindow.tryDestroy()
        time.sleep(actionWaitTime)

        self.assertIsNone(searchForWindowByTitle(firstWindowTitle))
        self.assertIsNone(searchForWindowByTitle(secondWindowTitle))


@unittest.skipIf(not run_T_WindowMessage, "Not Testing")
class T_WindowMessage(unittest.TestCase):

    def test_canSendWindowMessage(self):
        # fmt: off
        # fmt: on

        # this case checks with the WM_SETTEXT and the getWindowTextFunction
        first = createAndGetWindowRef("Window!!", "This is a window!")
        newText = "This is the new Window Text"
        time.sleep(windowCreateDestroyTime)

        first.sendWindowMessage(
            WM_SETTEXT, lParam=newText, tryWaitForMessageToProcess=True
        )
        time.sleep(windowCreateDestroyTime)

        first.tryActivate()
        time.sleep(actionWaitTime)

        newWindow = searchForWindowByTitle(newText)
        self.assertIsNotNone(newWindow)

        newWindow.tryDestroy()
        time.sleep(windowCreateDestroyTime)
        self.assertIsNone(searchForWindowByTitle(first.windowTitle))


@unittest.skipIf(not run_T_WindowManager, "Not Testing")
class T_WindowManagerTests(unittest.TestCase):

    def test_doesWindowExistIsItForeground(self):
        first = createAndGetWindowRef("this is a window")
        time.sleep(windowCreateDestroyTime)
        second = createAndGetWindowRef("this is the current window")
        time.sleep(windowCreateDestroyTime)

        second.tryActivate(withMinimize=True)
        time.sleep(actionWaitTime)

        self.assertEqual(getForegroundWindowAsObject().windowTitle, second.windowTitle)

        isWindowAlive = doesWindowExistIsItForeground(
            first.windowTitle, trySetForegroundIfNot=False
        )
        self.assertEqual(isWindowAlive, (True, False))
        #                                  ^     ^
        #                            isAlive     isForeground

        time.sleep(actionWaitTime)
        isWindowAlive = doesWindowExistIsItForeground(first.windowTitle)
        self.assertEqual(isWindowAlive, (True, True))
        #                                  ^     ^
        #                            isAlive     isForeground

        first.tryDestroy()
        time.sleep(windowCreateDestroyTime)
        self.assertIsNone(searchForWindowByTitle(first.windowTitle))

        second.tryDestroy()
        time.sleep(windowCreateDestroyTime)
        self.assertIsNone(searchForWindowByTitle(second.windowTitle))


@unittest.skipIf(not run_T_WindowPosition, "Skipped")
class T_WindowPostionTests(unittest.TestCase):

    def test_doesWindowGoBackToCorrectPosition(self):
        from win32gui import GetWindowRect

        windowName = "first"

        first = createAndGetWindowRef(windowName)
        time.sleep(windowCreateDestroyTime)
        originalPos = Rect(*GetWindowRect(first.hwnd))

        first.tryActivate()
        time.sleep(actionWaitTime)
        curPos = Rect(*GetWindowRect(first.hwnd))

        self.assertEqual(originalPos, curPos)

        first.tryDestroy()
        time.sleep(windowCreateDestroyTime)
        self.assertIsNone(searchForWindowByTitle(windowName))


@unittest.skipIf(not run_T_EventsTest, "Skipped")
class T_EventsTest(unittest.TestCase):

    def test_spinlockORthreadWaitTest(self):
        win = State(None)
        event = Event()
        testWindowName = f"Window: {uuid1()}"

        def handleWindow(window: Window):
            win.setVal(window)
            event.set()

        thread = event_windowCreated(handleWindow, {"keyword": testWindowName})
        testWindow = createAndGetWindowRef(testWindowName, "This is the message")

        event.wait()

        self.assertIsNotNone(win.val)
        self.assertTrue(thread.isStopped, "Thread stopped")

        testWindow.tryDestroy()
        time.sleep(windowCreateDestroyTime)
        self.assertIsNone(searchForWindowByTitle(testWindowName))

    def test_eventChain(self):
        state = State(False)
        event = Event()
        windowName = f"Window: {uuid1()}"

        def eventZero(window):
            self.assertEqual(windowName, window.windowTitle)
            eventZero_chainZero(window)

        def eventZero_chainZero(window):
            self.assertEqual(windowName, window.windowTitle)
            chainZero_chainZero(window)

        def chainZero_chainZero(window):
            self.assertEqual(windowName, window.windowTitle)
            chainZero_chainOne(window)

        def chainZero_chainOne(window):
            state.setVal(True)
            self.assertEqual(windowName, window.windowTitle)
            event.set()

        thread = event_windowCreated(eventZero, {"keyword": windowName})

        win = createAndGetWindowRef(windowName, "Message!")

        event.wait()

        self.assertTrue(state.val)

        self.assertIsNotNone(searchForWindowByTitle(windowName))
        self.assertTrue(thread.isStopped, "Thread stopped")

        win.tryDestroy()
        time.sleep(windowCreateDestroyTime)
        self.assertIsNone(searchForWindowByTitle(windowName))

    def test_timeout(self):
        start = time.time()
        thread = event_windowCreated(lambda window: None, {"keyword": "__EMPTY__"})

        thread.join()
        end = int(time.time() - start)

        self.assertAlmostEqual(end, 10)


@unittest.skipIf(not run_T_WindowHandlers, "Not Testing")
class T_SpecialWindowTitleHandlers(unittest.TestCase):

    def test_windowWithSpecialCharactersInTitle(self):
        specialTitle = "!@#$%^&*()_+|}{:?><,./;'[]\\=-`~"
        windowRef = createAndGetWindowRef(specialTitle)
        time.sleep(windowCreateDestroyTime)

        self.assertIsNotNone(windowRef)
        self.assertEqual(
            specialTitle,
            windowRef.windowTitle,
            f"\t- {specialTitle} != {windowRef.windowTitle}\n",
        )

        windowRef.tryDestroy()
        time.sleep(windowCreateDestroyTime)

        windowRef = searchForWindowByTitle(specialTitle)
        self.assertIsNone(windowRef)


@unittest.skipIf(not run_T_WindowHandlers, "Not Testing")
class T_ConcurrentWindowHandlers(unittest.TestCase):

    def test_concurrentWindowCreation(self):
        titles = ["Window 1", "Window 2", "Window 3"]
        windowRefs = []

        def create_window(title):
            windowRef = createAndGetWindowRef(title)
            self.assertIsNotNone(windowRef)
            self.assertEqual(title, windowRef.windowTitle)
            windowRefs.append(windowRef)

        threads = [Thread(target=create_window, args=(title,)) for title in titles]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        time.sleep(windowCreateDestroyTime)

        for windowRef in windowRefs:
            windowRef.tryDestroy()
            time.sleep(windowCreateDestroyTime)

        for title in titles:
            self.assertIsNone(searchForWindowByTitle(title))


@unittest.skipIf(not run_T_WindowHandlers, "Not Testing")
class T_InvalidHWNDHandlers(unittest.TestCase):

    def test_invalidHWND(self):
        invalidHWND = -1
        with self.assertRaises(pywinError):
            Window(invalidHWND, 0, 0)

        # Ensure no window is created with an invalid HWND
        self.assertIsNone(searchForWindowByTitle("Invalid HWND Window"))


@unittest.skipIf(not run_T_WindowPosition, "Not Testing")
class T_WindowPositionTests(unittest.TestCase):

    def test_windowPosition(self):
        from win32gui import GetWindowRect

        windowTitle = "Position Test Window"
        windowRef = createAndGetWindowRef(windowTitle)
        time.sleep(windowCreateDestroyTime)
        originalPos = Rect(*GetWindowRect(windowRef.hwnd))

        windowRef.tryActivate(withMinimize=True)
        time.sleep(actionWaitTime)
        currentPos = Rect(*GetWindowRect(windowRef.hwnd))

        self.assertEqual(originalPos, currentPos)

        windowRef.tryDestroy()
        time.sleep(windowCreateDestroyTime)
        self.assertIsNone(searchForWindowByTitle(windowTitle))


os.system("cls")
unittest.main(verbosity=5)
