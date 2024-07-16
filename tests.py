import os
import time
import unittest

from threading import Thread
from tkinter.messagebox import showinfo
from lib.WindowHandler import getForegroundWindowAsObject, searchForWindowByTitle


class Test_WindowHandlers(unittest.TestCase):

    def createAndGetWindowRef(self, title: str, message: str = None):
        def showMessageBox(title: str, content: str = None):
            Thread(target=lambda: showinfo(title, content or "Hello World")).start()
            time.sleep(0.4)
            return title

        return searchForWindowByTitle(showMessageBox(title, message))

    def test_canCloseWindow(self):
        windowTitle = "Test Window"
        windowRef = self.createAndGetWindowRef(windowTitle)

        self.assertIsNotNone(windowRef)
        self.assertEqual(
            windowTitle,
            windowRef.windowTitle,
            f"\t- {windowTitle} != {windowRef.windowTitle}\n",
        )

        windowRef.tryDestroy()

        windowRef = searchForWindowByTitle(windowTitle)
        self.assertIsNone(windowRef)

    def test_canGetWindowReference(self):
        windowTitle = "Get this Window Ref"
        windowRef = self.createAndGetWindowRef(windowTitle)

        self.assertIsNotNone(windowRef)
        self.assertEqual(
            windowTitle,
            windowRef.windowTitle,
            f"\t- {windowTitle} != {windowRef.windowTitle}\n",
        )

        windowRef.tryDestroy()

    def test_canSwitchWindow(self):
        firstWindowTitle = "First"
        firstWindow = self.createAndGetWindowRef(firstWindowTitle)

        secondWindowTitle = "Second"
        secondWindow = self.createAndGetWindowRef(secondWindowTitle)

        firstWindow.tryActivate(withMinimize=False)
        self.assertEqual(getForegroundWindowAsObject().windowTitle, firstWindowTitle)

        secondWindow.tryActivate(withMinimize=False)
        self.assertEqual(getForegroundWindowAsObject().windowTitle, secondWindowTitle)

        firstWindow.tryDestroy()
        secondWindow.tryDestroy()

        self.assertIsNone(searchForWindowByTitle(firstWindowTitle))
        self.assertIsNone(searchForWindowByTitle(secondWindowTitle))


os.system("cls")
unittest.main(verbosity=1)
