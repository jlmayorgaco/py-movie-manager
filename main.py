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
## ---- PyMovieManager CLI Loader ---------------------------------------------- ##
## ------------------------------------------------------------------------------ ##
import os
import logging
import argparse
from dotenv import load_dotenv

from config.GenresConfig import GenresEnum
from src.domain.classes.ConfigClass import Config
from src.domain.classes.ScrapperServiceIMDB import ScrapperServiceIMDB
from src.domain.classes.FilterServiceDefaultClass import FilterServiceDefault
from src.domain.classes.FileSystemMacOSClass import FileSystemMacOS
from src.domain.classes.FileSystemSynologyOSClass import FileSystemSynologyOS
from src.domain.classes.MovieManagerClass import MovieManager

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

## ------------------------------------------------------------------------------ ##
## ---- Initialize Services ---------------------------------------------------- ##
## ------------------------------------------------------------------------------ ##

def initialize_movie_manager_services(config_path: str, os_type: str):
    """Initialize and configure all services."""
    try:
        # Load configuration
        cnfg = Config(config_path)
        cnfg.setGenres(GenresEnum)

        logger.info(f"🧾 Loaded config from: {config_path}")
        logger.info("🔧 Config values:")
        logger.info(f"  directory_raw  : {cnfg.directory_raw}")
        logger.info(f"  directory_temp : {cnfg.directory_temp}")
        logger.info(f"  directory_vose : {cnfg.directory_vose}")
        logger.info(f"  dry_run        : {cnfg.dry_run}")

            # Scrapper Service
        imdb = ScrapperServiceIMDB()
        imdb.setApiKey(os.getenv("IMDB_API_KEY", "default_api_key"))
        logger.info(f"🔑 IMDb API key loaded: {imdb.api_key}")

        # Filter Service
        ff = FilterServiceDefault()
        ff.setGenres(cnfg.getGenres())
        ff.setGenreSearchTag(os.getenv("GENRE_TAG", "[g-*]"))
        ff.setDirectorSearchTag(os.getenv("DIRECTOR_TAG", "[d-*]"))
        logger.info("🔍 Filter service initialized with tags and genres")

        # File System Service
        if os_type == "synology":
            fs = FileSystemSynologyOS()
        elif os_type == "mac":
            fs = FileSystemMacOS()
        else:
            raise ValueError(f"Unsupported OS: {os_type}")

        fs.setConfig(cnfg)
        fs.setFilter(ff)
        logger.info(f"💽 File system service initialized for {os_type}")

        # Movie Manager
        movieManager = MovieManager()
        movieManager.setServiceConfig(cnfg)
        movieManager.setServiceFilter(ff)
        movieManager.setServiceFileSystem(fs)
        movieManager.setServiceScrapper(imdb)
        logger.info("🎬 MovieManager service initialized and configured")

        return movieManager
    except Exception as e:
        logger.error(f"❌ Initialization error: {e}")
        raise


def run_movie_manager(movieManager):
    """Execute the main workflow for movie management."""
    try:
        logger.info(f"🚦 DRY RUN MODE = {movieManager.config.get('dry_run')}")

        movieManager.start()
        logger.info("✅ Workflow start completed")

        movieManager.creating_temp_genres()
        logger.info("✅ Workflow creating_temp_genres completed")

        movieManager.moving_to_temp()
        logger.info("✅ Workflow moving_to_temp completed")

        movieManager.renaming_in_temp()
        logger.info("✅ Workflow renaming_in_temp completed")

        movieManager.moving_to_vose()
        logger.info("✅ Workflow moving_to_vose completed")

    except Exception as e:
        logger.error(f"❌ Workflow error: {e}")


## ------------------------------------------------------------------------------ ##
## ---- Entry Point with CLI Arguments ----------------------------------------- ##
## ------------------------------------------------------------------------------ ##

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PyMovieManager Runner")
    parser.add_argument("--sandbox", action="store_true", help="Use sandbox config")
    parser.add_argument("--os", choices=["mac", "synology"], default="mac", help="Operating system environment")

    args = parser.parse_args()

    config_file = "config/config.sandbox.json" if args.sandbox else "config/config.json"
    logger.info(f"▶️ Starting PyMovieManager [OS: {args.os}] [Config: {config_file}]")

    try:
        movieManager = initialize_movie_manager_services(config_file, args.os)
        run_movie_manager(movieManager)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
