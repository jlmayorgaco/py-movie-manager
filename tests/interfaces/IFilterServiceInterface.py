from abc import abstractmethod
from abc import ABCMeta

class IFilterService(metaclass=ABCMeta):

    def __init__(self):
        pass

    @abstractmethod
    def setGenreSearchTag(tag: str):
        pass

    @abstractmethod
    def setDirectorSearchTag(tag: str):
        pass