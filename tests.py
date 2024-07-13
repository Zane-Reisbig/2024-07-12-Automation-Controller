import time

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

    print(f"{i.windowTitle[0:-min(len(i.windowTitle), 10)]} is foreground: ", end="")
    print(i.isForeground())
    print()
    countDown(2)

if not currentWindow.tryActivate():
    raise Exception("How did we fail from the calling thread 🙀")
