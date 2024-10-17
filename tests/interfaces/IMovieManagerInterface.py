from abc import abstractmethod
from abc import ABCMeta

class IMovieManager(metaclass=ABCMeta):

    def __init__(self):
        pass

    @abstractmethod
    def setServiceConfig(config):
        pass

    @abstractmethod
    def setServiceFileSystem(filesystem):
        pass

    @abstractmethod
    def setServiceFilter(filterservice):
        pass

    @abstractmethod
    def setServiceScrapper(scrapper):
        pass

    @abstractmethod
    def start():
        pass
