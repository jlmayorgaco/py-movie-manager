from enum import Enum

from src.domain.interfaces.IConfigInterface import IConfig
from src.domain.interfaces.IScrapperInterface import IScrapper
from src.domain.interfaces.IFileSystemInterface import IFileSystem
from src.domain.interfaces.IFilterServiceInterface import IFilterService

from src.domain.classes.ConfigClass import Config
from src.domain.classes.ScrapperServiceIMDB import ScrapperServiceIMDB
from src.domain.classes.FilterServiceDefaultClass import FilterServiceDefault
from src.domain.classes.FileSystemMacOSClass import FileSystemMacOS
from src.domain.classes.MovieManagerClass import MovieManager

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



## ------------------------------------------------------------------------------ ##
## ---- Mod::Config Service ----------------------------------------------------- ##
## ------------------------------------------------------------------------------ ##
cnfg = Config()
cnfg.setDirectorySource("/Volumes/DX517/Movies/[Movies] Filmoteca/[Movies] Filmoteca VOSE RAW/RAW")
cnfg.setDirectoryTarget("/Volumes/DX517/Movies/[Movies] Filmoteca/[Movies] Filmoteca VOSE")
cnfg.setGenres(GenresEnum)

print(' CONFIG .... DONE ')
print(cnfg)
## ------------------------------------------------------------------------------ ##



## ------------------------------------------------------------------------------ ##
## ---- Mod::Scrapper Service --------------------------------------------------- ##
## ------------------------------------------------------------------------------ ##
imdb = ScrapperServiceIMDB()
imdb.setApiKey('sdfasd')

print(' SCRAPPER .... DONE ')
print(imdb)

## ------------------------------------------------------------------------------ ##



## ------------------------------------------------------------------------------ ##
## ---- Mod::Filter Service ----------------------------------------------------- ##
## ------------------------------------------------------------------------------ ##
ff = FilterServiceDefault()
ff.setGenres(cnfg.getGenres())
ff.setGenreSearchTag('[g-*]')
ff.setDirectorSearchTag('[d-*]')

print(' FilterService .... DONE ')
print(ff)
## ------------------------------------------------------------------------------ ##



## ------------------------------------------------------------------------------ ##
## ---- Mod::Mac OS FileSystem -------------------------------------------------- ##
## ------------------------------------------------------------------------------ ##
fs = FileSystemMacOS()
fs.setConfig(cnfg)
fs.setFilter(ff)

print(' FileSystem .... DONE ')
print(fs)
## ------------------------------------------------------------------------------ ##





## ------------------------------------------------------------------------------ ##
## ---- Mod::Mac OS FileSystem -------------------------------------------------- ##
## ------------------------------------------------------------------------------ ##
movieManager = MovieManager()
movieManager.setServiceConfig(cnfg)
movieManager.setServiceFilter(ff)
movieManager.setServiceFileSystem(fs)
movieManager.setServiceScrapper(imdb)

movieManager.start()
movieManager.creating_temp()
#movieManager.moving_to_temp()
#movieManager.renaming_in_temp()
#movieManager.moving_to_vose()
#movieManager.deleting_temp()

## ------------------------------------------------------------------------------ ##
