from abc import abstractmethod
from abc import ABCMeta
class IScrapper(metaclass=ABCMeta):

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def getMovieByNameAndYear(self, name, year):
        pass


