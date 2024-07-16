from lib.WindowHandler import searchForWindowByTitle


class BaseActionableWindow:
    def __init__(self, windowKeyWord: str, keywordFilter: list = list()):
        self.windowKeyWord = windowKeyWord
        self.keywordFilter = keywordFilter

    def open(self):
        raise NotImplementedError("No Implementation")

    def close(self):
        raise NotImplementedError("No Implementation")

    def isOpen(self):
        haveWindow = searchForWindowByTitle(self.windowKeyWord, self.keywordFilter)
        if haveWindow:
            return haveWindow

        return False
