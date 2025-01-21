## ------------------------------------------------------------------------------ ##
## ---- PyMovieManager ---------------------------------------------------------- ##
## ------------------------------------------------------------------------------ ##
"""
PyMovieManager: A Python-based tool for organizing and managing movie files 
for use with a Plex Media Server. This script orchestrates the initialization 
and execution of core services required to identify, filter, and move movies 
into genre-based folders.

Author: Jorge Luis Mayorga Taborda (jlmayorgaco)
Date: January 20, 2025
Version: 1.0.0
License: MIT License
GitHub: https://github.com/jlmayorgaco/py-movie-manager
Dependencies: See requirements.txt or pyproject.toml.

### Overview
This script serves as the entry point for the PyMovieManager project. It 
leverages modular components to separate concerns, ensuring clean code, 
scalability, and maintainability. 

### Architecture
1. **Core Components**:
   - **ConfigClass**: Manages configurations such as source and target directories.
   - **ScrapperServiceIMDB**: Integrates IMDb API to enrich movie metadata.
   - **FilterServiceDefaultClass**: Handles filtering and tag management for genres and directors.
   - **FileSystemMacOSClass**: Abstracts filesystem operations like moving and renaming files.
   - **MovieManagerClass**: The central manager that coordinates all services.

2. **Workflow**:
   - Initialize all services and inject dependencies.
   - Configure the source and target directories for movies.
   - Identify movies in the raw folder, filter and rename them, and organize them 
     into temporary genre-based folders.
   - Finalize the process by moving movies to the production folder while 
     preserving existing structures.

3. **Design Principles**:
   - **Modularity**: Each service is responsible for a distinct part of the workflow.
   - **Dependency Injection**: Services are decoupled and injected into the manager.
   - **Clean Code**: Follows DRY, KISS, and SOLID principles to ensure maintainability.
   - **Scalability**: Supports future extension, such as additional scrapers or platforms.
"""
## ------------------------------------------------------------------------------ ##

## ------------------------------------------------------------------------------ ##
## ---- Dependencies ------------------------------------------------------------ ##
## ------------------------------------------------------------------------------ ##
import os
import logging

from enum import Enum
from dotenv import load_dotenv

from config.GenresConfig import GenresEnum

from src.domain.interfaces.IConfigInterface import IConfig
from src.domain.interfaces.IScrapperInterface import IScrapper
from src.domain.interfaces.IFileSystemInterface import IFileSystem
from src.domain.interfaces.IFilterServiceInterface import IFilterService

from src.domain.classes.ConfigClass import Config
from src.domain.classes.ScrapperServiceIMDB import ScrapperServiceIMDB
from src.domain.classes.FilterServiceDefaultClass import FilterServiceDefault
from src.domain.classes.FileSystemMacOSClass import FileSystemMacOS
from src.domain.classes.MovieManagerClass import MovieManager

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
## ------------------------------------------------------------------------------ ##


try:
    ## ------------------------------------------------------------------------------ ##
    ## ---- Mod::Config Service ----------------------------------------------------- ##
    ## ------------------------------------------------------------------------------ ##
    cnfg = Config()
    cnfg.setDirectorySource(os.getenv("SOURCE_DIR", "/source"))
    cnfg.setDirectoryTarget(os.getenv("TARGET_DIR", "/target"))
    cnfg.setGenres(GenresEnum)

    logger.info("CONFIG .... DONE")
    logger.info(cnfg)
    ## ------------------------------------------------------------------------------ ##



    ## ------------------------------------------------------------------------------ ##
    ## ---- Mod::Scrapper Service --------------------------------------------------- ##
    ## ------------------------------------------------------------------------------ ##
    imdb = ScrapperServiceIMDB()
    imdb.setApiKey(os.getenv("IMDB_API_KEY", "default_api_key"))

    logger.info("SCRAPPER .... DONE")
    logger.info(imdb)
    ## ------------------------------------------------------------------------------ ##



    ## ------------------------------------------------------------------------------ ##
    ## ---- Mod::Filter Service ----------------------------------------------------- ##
    ## ------------------------------------------------------------------------------ ##
    ff = FilterServiceDefault()
    ff.setGenres(cnfg.getGenres())
    ff.setGenreSearchTag(os.getenv("GENRE_TAG", "[g-*]"))
    ff.setDirectorSearchTag(os.getenv("DIRECTOR_TAG", "[d-*]"))

    logger.info("FilterService .... DONE")
    logger.info(ff)
    ## ------------------------------------------------------------------------------ ##



    ## ------------------------------------------------------------------------------ ##
    ## ---- Mod::Mac OS FileSystem -------------------------------------------------- ##
    ## ------------------------------------------------------------------------------ ##
    fs = FileSystemMacOS()
    fs.setConfig(cnfg)
    fs.setFilter(ff)

    logger.info("FileSystem .... DONE")
    logger.info(fs)
    ## ------------------------------------------------------------------------------ ##



    ## ------------------------------------------------------------------------------ ##
    ## ---- Mod::MovieManager ------------------------------------------------------- ##
    ## ------------------------------------------------------------------------------ ##
    movieManager = MovieManager()
    movieManager.setServiceConfig(cnfg)
    movieManager.setServiceFilter(ff)
    movieManager.setServiceFileSystem(fs)
    movieManager.setServiceScrapper(imdb)

    logger.info(" ")
    logger.info("======================================")
    logger.info("===  START::movieManager =============")
    logger.info("======================================")
    logger.info(" ")

    def run_movie_manager():
        try:
            movieManager.start()
            movieManager.creating_temp_genres()
            movieManager.moving_to_temp()
            movieManager.renaming_in_temp()
            # movieManager.moving_to_vose()
            # movieManager.deleting_temp()
        except Exception as e:
            logger.error(f"Workflow error: {e}")

    ## ------------------------------------------------------------------------------ ##
except Exception as e:
    logger.error(f"An error occurred: {e}")


if __name__ == "__main__":
    run_movie_manager()