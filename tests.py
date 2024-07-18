import os
import time
import unittest

from threading import Thread
from tkinter.messagebox import showinfo
from lib.WindowHandler.managers import (
    searchForWindowByTitle,
    getForegroundWindowAsObject,
)

run_T_WindowHandlers = True
run_T_WindowMessage = True


@unittest.skipIf(not run_T_WindowHandlers, "Not Testing")
class T_WindowHandlers(unittest.TestCase):
    timeSleep = 1
    timeWindowCreateDestroy = 0.4

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
    timeSleep = 1
    timeWindowCreateDestroy = 0.4

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


os.system("cls")
unittest.main(verbosity=5)
