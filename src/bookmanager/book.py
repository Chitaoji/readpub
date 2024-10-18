"""
Contains the container for a book: Book, etc.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""


class Book:
    def __init__(self, filedict: dict[str, bytes]) -> None:
        self.filedict = filedict
