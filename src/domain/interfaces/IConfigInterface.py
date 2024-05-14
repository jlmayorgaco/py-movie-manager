from abc import abstractmethod
from abc import ABCMeta

class IConfig(metaclass=ABCMeta):

    def __init__(self):
        pass

    @abstractmethod
    def setDirectorySource(path):
        pass

    @abstractmethod
    def setDirectoryTarget(path):
        pass

    @abstractmethod
    def setGenres(genres):
        pass
