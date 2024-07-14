import time


def canGetWindowsTest():
    from lib.WindowHandler import (
        searchForWindowByTitle,
        searchForWindowsByTitle,
        getForegroundWindowAsObject,
    )

    print(" " * 100, end="")
    print()

    def countDown(_from=5):
        for i in range(_from, 0, -1):
            print(i, end="...")
            time.sleep(1)

        print("GO!")

    # This is a single window search
    foo = searchForWindowByTitle("Discord")
    print(foo)
    print()
    countDown()

    # This is a multi-window search
    bar = searchForWindowsByTitle("Firefox", ignore=["Youtube", "YouTube", "Twitch"])
    # bar = searchForWindowsByTitle("Chrome", ignore=["Youtube", "YouTube", "Twitch"])
    print(bar)
    print()
    countDown()

    #
    # Quick Switching Windows
    #

    # Get starting window so we can end on that one
    currentWindow = getForegroundWindowAsObject()
    print(currentWindow)
    print()
    countDown()

    if not foo.tryActivate():
        raise Exception("So far so bad.")

    print(f"{foo.windowTitle[:-min(len(foo.windowTitle), 10)]} is foreground", end="")
    print(foo.isForeground())
    print()
    countDown(3)

    for i in bar:
        if not i.tryActivate():
            raise Exception("This is not chilling.")

        print(
            f"{i.windowTitle[0:-min(len(i.windowTitle), 10)]} is foreground: ", end=""
        )
        print(i.isForeground())
        print()
        countDown(2)

    if not currentWindow.tryActivate():
        raise Exception("How did we fail from the calling thread 🙀")


def actionableWindowTest():
    from lib.ControllableWindow.BaseWindow import BaseActionableWindow
    from tkinter.messagebox import showinfo
    from threading import Thread

    from keyboard import send

    class OpenClaimWindowNoImp(BaseActionableWindow):
        def __init__(self):
            super().__init__("Open")

        def open(self):
            super().open()

        # def close(self):
        #     super().close()

        # def isOpen(self):
        #     super().isOpen()

    class OpenWindowWithImp(BaseActionableWindow):
        def __init__(self):
            super().__init__("Open")

        def open(self):
            x = Thread(target=lambda: showinfo("Open", "This is a popup"))
            x.start()
            time.sleep(1)

        def close(self):
            isWindowOpen = super().isOpen()
            if not isWindowOpen:
                return True

            if not isWindowOpen.tryActivate(withMinimize=False):
                return False

            send("esc")
            time.sleep(1)
            return super().isOpen()

    x = OpenClaimWindowNoImp()

    try:
        x.open()
    except NotImplementedError:
        print("Open Fail")

    try:
        x.close()
    except NotImplementedError:
        print("Close Fail")

    y = OpenWindowWithImp()

    print("trying to open")
    y.open()
    print("checking if open")
    y.isOpen()
    print("trying to close")
    y.close()
    print("is it open still?")
    print(y.isOpen())


print("\n\n")

# canGetWindowsTest()
actionableWindowTest()
