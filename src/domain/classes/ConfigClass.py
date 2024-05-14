from enum import Enum

from ..interfaces.IConfigInterface import IConfig
class GenresEnum(Enum):
    ACTION = 'Action'
    ADVENTURE = 'Adventure'
    ANIMATION = 'Animation'
    BIOGRAPHY = 'Biography'
    COMEDY = 'Comedy'
    CRIME = 'Crime'
    DOCUMENTARY = 'Documentary'
    DRAMA = 'Drama'
    FAMILY = 'Family'
    FANTASY = 'Fantasy'
    HISTORY = 'History'
    HORROR = 'Horror'
    MUSIC = 'Music'
    MYSTERY = 'Mystery'
    ROMANCE = 'Romance'
    SCIENCE_FICTION = 'Science Fiction'
    SPORT = 'Sport'
    THRILLER = 'Thriller'
    WAR = 'War'
    WESTERN = 'Western'


class Config(IConfig):

    def __init__(self):
        self.directory_raw = ''
        self.directory_vose = ''
        self.genres = None

    def __str__(self):
        genres_str = ', '.join([genre.name for genre in self.genres])
        return f''' 
        Config::Directory Source <{self.directory_raw}> 
        Config::Directory Target <{self.directory_vose}>
        Config::Genres <{genres_str}>
        '''

    def setDirectorySource(self, path):
        self.directory_raw = path
        return 1

    def setDirectoryTarget(self, path):
        self.directory_vose = path
        return 1

    def setGenres(self, genres: GenresEnum):
        self.genres = genres
        return 1

    def getGenres(self) -> list[str]:
        return [genre.name for genre in self.genres]
