import os
import sys
import time
import unittest
import logging

from win32con import WM_SETTEXT

from threading import Thread, Lock
from tkinter.messagebox import showinfo
from uuid import uuid1
from lib.WindowHandler import Window
from lib.WindowHandler.managers import (
    event_windowCreated,
    searchForWindowByTitle,
    getForegroundWindowAsObject,
    doesWindowExistIsItForeground,
    Rect,
    State,
)

# fmt: off
run_T_WindowHandlers = True
run_T_WindowMessage  = True
run_T_WindowManager  = True
run_T_WindowPosition = True
run_T_EventsTest     = True
# fmt: on

actionWaitTime = 0.2
windowCreateDestroyTime = 0.4


def createAndGetWindowRef(title: str, message: str = None):
    def showMessageBox(title: str, content: str = None):
        Thread(target=lambda: showinfo(title, content or "Hello World")).start()
        time.sleep(windowCreateDestroyTime)
        return title

    return searchForWindowByTitle(showMessageBox(title, message))


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

        firstWindow.tryActivate(withMinimize=False)
        self.assertEqual(getForegroundWindowAsObject().windowTitle, firstWindowTitle)

        time.sleep(actionWaitTime)

        secondWindow.tryActivate(withMinimize=False)
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
            WM_SETTEXT,
            lParam=newText,
        )
        time.sleep(actionWaitTime)

        first.tryActivate(withMinimize=False)
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
        second = createAndGetWindowRef("this is the current window")
        time.sleep(windowCreateDestroyTime)

        second.tryActivate(withMinimize=False)
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

        first = createAndGetWindowRef("first")
        time.sleep(windowCreateDestroyTime)
        originalPos = Rect(*GetWindowRect(first.hwnd))

        first.tryActivate(withMinimize=True)
        time.sleep(actionWaitTime)
        curPos = Rect(*GetWindowRect(first.hwnd))

        self.assertEqual(originalPos, curPos)

        first.tryDestroy()


@unittest.skipIf(not run_T_EventsTest, "Skipped")
class T_EventsTest(unittest.TestCase):

    def test_spinlockORthreadWaitTest(self):
        win = State(None)
        testWindowName = f"Window: {uuid1()}"

        def handleWindow(window: Window):
            win.setVal(window)

        thread = event_windowCreated(handleWindow, {"keyword": testWindowName})
        testWindow = createAndGetWindowRef(testWindowName, "This is the message")

        while win.val == None:
            time.sleep(1)

        self.assertIsNotNone(win.val)
        self.assertTrue(thread.isStopped, "Thread stopped")

        testWindow.tryDestroy()
        self.assertIsNone(searchForWindowByTitle(testWindowName))

    def test_eventChain(self):
        state = State(False)
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

        thread = event_windowCreated(eventZero, {"keyword": windowName})

        win = createAndGetWindowRef(windowName, "Message!")

        while False == state.val:
            time.sleep(1)

        self.assertTrue(state.val)

        self.assertIsNotNone(searchForWindowByTitle(windowName))
        self.assertTrue(thread.isStopped, "Thread stopped")

        win.tryDestroy()
        self.assertIsNone(searchForWindowByTitle(windowName))


os.system("cls")
unittest.main(verbosity=5)
