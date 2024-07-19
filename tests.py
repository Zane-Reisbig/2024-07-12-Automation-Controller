import os
import time
import unittest

from threading import Thread
from tkinter.messagebox import showinfo
from lib.WindowHandler.managers import (
    searchForWindowByTitle,
    getForegroundWindowAsObject,
    doesWindowExistIsItForeground,
    Rect,
)

run_T_WindowHandlers = False
WindowHandlers_timeSleepActions = 1
WindowHandlers_timeCreateDestroy = 0.4

run_T_WindowMessage = False
WindowMessage_timeSleepActions = 1
WindowMessage_timeCreateDestroy = 0.4

run_T_WindowManager = False
WindowManager_timeSleepActions = 1
WindowManager_timeCreateDestroy = 0.4

run_T_WindowPosition = True
WindowPosition_timeSleepActions = 1
WindowPosition_timeCreateDestroy = 0.4


@unittest.skipIf(not run_T_WindowHandlers, "Not Testing")
class T_WindowHandlers(unittest.TestCase):
    timeSleep = WindowHandlers_timeSleepActions
    timeWindowCreateDestroy = WindowHandlers_timeCreateDestroy

    def createAndGetWindowRef(self, title: str, message: str = None):
        def showMessageBox(title: str, content: str = None):
            Thread(target=lambda: showinfo(title, content or "Hello World")).start()
            time.sleep(self.timeWindowCreateDestroy)
            return title

        return searchForWindowByTitle(showMessageBox(title, message))

    def test_canCloseWindow(self):
        windowTitle = "Test Window"
        windowRef = self.createAndGetWindowRef(windowTitle)

        time.sleep(self.timeSleep)

        self.assertIsNotNone(windowRef)
        self.assertEqual(
            windowTitle,
            windowRef.windowTitle,
            f"\t- {windowTitle} != {windowRef.windowTitle}\n",
        )

        windowRef.tryDestroy()
        time.sleep(self.timeWindowCreateDestroy)

        windowRef = searchForWindowByTitle(windowTitle)
        self.assertIsNone(windowRef)

    def test_canGetWindowReference(self):
        windowTitle = "Get this Window Ref"
        windowRef = self.createAndGetWindowRef(windowTitle)

        time.sleep(self.timeSleep)

        self.assertIsNotNone(windowRef)
        self.assertEqual(
            windowTitle,
            windowRef.windowTitle,
            f"\t- {windowTitle} != {windowRef.windowTitle}\n",
        )

        windowRef.tryDestroy()
        time.sleep(self.timeWindowCreateDestroy)

    def test_canSwitchWindow(self):
        firstWindowTitle = "First"
        firstWindow = self.createAndGetWindowRef(firstWindowTitle)

        time.sleep(self.timeSleep)

        secondWindowTitle = "Second"
        secondWindow = self.createAndGetWindowRef(secondWindowTitle)

        time.sleep(self.timeSleep)

        firstWindow.tryActivate(withMinimize=False)
        self.assertEqual(getForegroundWindowAsObject().windowTitle, firstWindowTitle)

        time.sleep(self.timeSleep)

        secondWindow.tryActivate(withMinimize=False)
        self.assertEqual(getForegroundWindowAsObject().windowTitle, secondWindowTitle)

        time.sleep(self.timeSleep)

        firstWindow.tryDestroy()
        time.sleep(self.timeWindowCreateDestroy)

        secondWindow.tryDestroy()
        time.sleep(self.timeWindowCreateDestroy)

        self.assertIsNone(searchForWindowByTitle(firstWindowTitle))
        self.assertIsNone(searchForWindowByTitle(secondWindowTitle))


@unittest.skipIf(not run_T_WindowMessage, "Not Testing")
class T_WindowMessage(unittest.TestCase):
    timeSleep = WindowHandlers_timeSleepActions
    timeWindowCreateDestroy = WindowHandlers_timeCreateDestroy

    def createAndGetWindowRef(self, title: str, message: str = None):
        def showMessageBox(title: str, content: str = None):
            Thread(target=lambda: showinfo(title, content or "Hello World")).start()
            time.sleep(self.timeWindowCreateDestroy)
            return title

        return searchForWindowByTitle(showMessageBox(title, message))

    def test_canSendWindowMessage(self):
        # fmt: off
        from win32con import WM_SETTEXT 
        # fmt: on

        # this case checks with the WM_SETTEXT and the getWindowTextFunction
        first = self.createAndGetWindowRef("Window!!", "This is a window!")
        newText = "This is the new Window Text"

        first.sendWindowMessage(
            WM_SETTEXT,
            lParam=newText,
        )

        first.tryActivate(withMinimize=False)

        newWindow = searchForWindowByTitle(newText)
        self.assertIsNotNone(newWindow)

        newWindow.tryDestroy()
        self.assertIsNone(searchForWindowByTitle(first.windowTitle))


@unittest.skipIf(not run_T_WindowManager, "Not Testing")
class T_WindowManagerTests(unittest.TestCase):

    timeSleep = WindowManager_timeSleepActions
    timeWindowCreateDestroy = WindowManager_timeCreateDestroy

    def createAndGetWindowRef(self, title: str, message: str = None):
        def showMessageBox(title: str, content: str = None):
            Thread(target=lambda: showinfo(title, content or "Hello World")).start()
            time.sleep(self.timeWindowCreateDestroy)
            return title

        return searchForWindowByTitle(showMessageBox(title, message))

    def test_doesWindowExistIsItForeground(self):
        first = self.createAndGetWindowRef("this is a window")
        second = self.createAndGetWindowRef("this is the current window")
        time.sleep(self.timeWindowCreateDestroy)

        second.tryActivate(withMinimize=False)
        time.sleep(self.timeSleep)

        self.assertEqual(getForegroundWindowAsObject().windowTitle, second.windowTitle)

        isWindowAlive = doesWindowExistIsItForeground(
            first.windowTitle, trySetForegroundIfNot=False
        )
        self.assertEqual(isWindowAlive, (True, False))
        #                                  ^     ^
        #                            isAlive     isForeground

        time.sleep(self.timeSleep)
        isWindowAlive = doesWindowExistIsItForeground(first.windowTitle)
        self.assertEqual(isWindowAlive, (True, True))
        #                                  ^     ^
        #                            isAlive     isForeground

        first.tryDestroy()
        time.sleep(self.timeWindowCreateDestroy)
        self.assertIsNone(searchForWindowByTitle(first.windowTitle))

        second.tryDestroy()
        time.sleep(self.timeWindowCreateDestroy)
        self.assertIsNone(searchForWindowByTitle(second.windowTitle))


@unittest.skipIf(not run_T_WindowPosition, "Skipped")
class T_WindowPostionTests(unittest.TestCase):
    timeSleep = WindowPosition_timeSleepActions
    timeWindowCreateDestroy = WindowPosition_timeCreateDestroy

    def createAndGetWindowRef(self, title: str, message: str = None):
        def showMessageBox(title: str, content: str = None):
            Thread(target=lambda: showinfo(title, content or "Hello World")).start()
            time.sleep(self.timeWindowCreateDestroy)
            return title

        return searchForWindowByTitle(showMessageBox(title, message))

    def test_doesWindowGoBackToCorrectPosition(self):
        from win32gui import GetWindowRect

        first = self.createAndGetWindowRef("first")
        time.sleep(self.timeWindowCreateDestroy)
        originalPos = Rect(*GetWindowRect(first.hwnd))

        first.tryActivate()
        time.sleep(self.timeSleep)
        curPos = Rect(*GetWindowRect(first.hwnd))

        self.assertEqual(originalPos, curPos)


os.system("cls")
unittest.main(verbosity=5)
