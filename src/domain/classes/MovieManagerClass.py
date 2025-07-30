import os
import logging
from tqdm import tqdm
from src.domain.interfaces.IMovieManagerInterface import IMovieManager
from src.domain.classes.ConfigClass import Config
class MovieManager(IMovieManager):
    """
    MovieManager: A service to organize and manage movie files based on genres.
    """

    # Constants
    TEMP_DIR_NAME = "__TMM_TEMP__"

    def __init__(self):
        """
        Initialize the MovieManager with default services.
        """
        self.configService = None
        self.scrapperService = None
        self.filterService = None
        self.fileSystemService = None

    def __str__(self) -> str:
        """
        String representation of the configured services.
        """
        return f"""
        MovieManager::ConfigService <{self.configService}>
        MovieManager::ScrapperService <{self.scrapperService}>
        MovieManager::FilterService <{self.filterService}>
        MovieManager::FileSystemService <{self.fileSystemService}>
        """

    # Setter methods for services
    def setServiceConfig(self, configService: Config) -> None:
        self.configService = configService

    def setServiceFilter(self, filterService) -> None:
        self.filterService = filterService

    def setServiceFileSystem(self, filesystemService) -> None:
        self.fileSystemService = filesystemService

    def setServiceScrapper(self, scrapperService) -> None:
        self.scrapperService = scrapperService

    # Core workflow methods
    def start(self) -> None:
        """
        Initialize the workflow by navigating to the RAW directory and setting up TEMP.
        """
        logger = logging.getLogger(__name__)
        raw_path = self.configService.getDirectorySource()
        temp_path = self._get_temp_path(raw_path)

        self.fileSystemService.cd(raw_path)
        self._prepare_temp_directory(temp_path)

    def creating_temp_genres(self) -> None:
        """
        Create genre directories in the TEMP directory.
        """
        logger = logging.getLogger(__name__)
        print("STEP::1 .... creating_temp_genres")
        
        # ✅ Use the getter method instead of a non-existent attribute
        temp_path = self._get_temp_path(self.configService.getDirectorySource())  
        logger.info(f"Temp path resolved: {temp_path}")

        if not self.fileSystemService:
            logger.error("File system service is not initialized!")
            return

        self.fileSystemService.ensure_directory_exists(temp_path)
        logger.info(f"Ensured temp directory exists: {temp_path}")

        # ✅ Change to the temp directory
        try:
            self.fileSystemService.cd(temp_path)
            logger.info(f"Changed working directory to: {temp_path}")
        except Exception as e:
            logger.error(f"Failed to change directory to {temp_path}: {e}")
            return

        # ✅ Get genres and create folders
        genres = self.configService.getGenres()
        logger.info(f"Genres to create: {genres}")

        for genre in genres:
            genre_path = os.path.join(temp_path, genre)
            logger.info(f"Creating genre directory: {genre_path}")
            
            try:
                self.fileSystemService.mkdir(genre)
                logger.info(f"Successfully created genre directory: {genre_path}")
            except OSError as e:
                logger.error(f"Failed to create directory for genre '{genre}': {e}")

    def moving_to_temp(self) -> None:
        """
        Move movie folders from RAW to TEMP, organizing by genre.
        """
        logger = logging.getLogger(__name__)
        print("\n\n\n\nSTEP::2 .... moving_to_temp\n\n\n\n")

        # ✅ Get the correct RAW directory path
        raw_path = self.configService.getDirectorySource()
        temp_path = self._get_temp_path(raw_path)

        # ✅ Change to RAW directory
        self.fileSystemService.cd(raw_path)
        folders = self.fileSystemService.get_folders()
        folders_filtered = self.filterService.filter_folders(folders)  # ✅ Filter folders

        total_folders = len(folders_filtered)
        logger.info(f"Found {len(folders)} folders in RAW, {total_folders} valid for processing.")

        # ✅ Enable preview mode (change to False to actually move)
        preview = False  

        # ✅ Use tqdm for a progress bar
        with tqdm(total=total_folders, desc="Moving Folders", unit="folder") as pbar:
            for index, folder in enumerate(folders_filtered, start=1):
                # ✅ Get genre from the filter service
                genre_from_folder = self.filterService.getGenreByFolderName(folder)
                most_likely_genre = self.filterService.getGenreByMostLikehood(genre_from_folder)

                # ✅ Skip folder if no genre is detected
                if not most_likely_genre:
                    logger.info(f"Skipping folder '{folder}': No matching genre found.")
                    pbar.update(1)
                    continue

                # ✅ Build source and destination paths
                from_path = self.fileSystemService.join(raw_path, folder)
                to_path = self.fileSystemService.join(temp_path, most_likely_genre)

                # ✅ Log progress with folder count
                logger.info(f"Processing folder {index} of {total_folders}: Moving '{folder}' to '{most_likely_genre}'")

                if preview:
                    logger.info(f"DRY RUN: Would move '{folder}' to '{most_likely_genre}'")
                else:
                    try:
                        self.fileSystemService.move(from_path, to_path)
                        logger.info(f"Successfully moved '{folder}' to '{to_path}' ({index} of {total_folders})")
                    except OSError as e:
                        logger.error(f"Failed to move '{folder}' to TEMP: {e}")

                # ✅ Update progress bar
                pbar.update(1)

    def renaming_in_temp(self) -> None:
        """
        Rename movie folders in TEMP to remove unnecessary tags while avoiding conflicts.
        """


        logger = logging.getLogger(__name__)
        print("\nSTEP::3 .... renaming_in_temp")

        # ✅ Get TEMP directory path
        temp_path = self._get_temp_path(self.configService.getDirectorySource())

        # ✅ Change to TEMP directory
        self.fileSystemService.cd(temp_path)
        genres = self.fileSystemService.get_folders()

        logger.info(f"Found {len(genres)} genre folders in TEMP.")

        # ✅ Use tqdm progress bar
        with tqdm(total=len(genres), desc="Renaming Movies", unit="folder") as pbar:
            for genre in genres:
                genre_path = self.fileSystemService.join(temp_path, genre)
                movies = self.fileSystemService.get_folders_at(genre_path)  # ✅ Get movie folders

                logger.info(f"Processing genre '{genre}' with {len(movies)} movies.")

                for movie in movies:
                    base_name = self.filterService.clean(movie)
                    new_name = base_name
                    old_path = self.fileSystemService.join(genre_path, movie)
                    new_path = self.fileSystemService.join(genre_path, new_name)

                    # ✅ Skip if names are the same
                    if old_path == new_path:
                        logger.info(f"Skipping '{movie}', already correctly named.")
                        continue

                    # ✅ If new name already exists, add suffix (1), (2), ...
                    counter = 1
                    while self.fileSystemService.exists(new_path):
                        new_name = f"{base_name} ({counter})"
                        new_path = self.fileSystemService.join(genre_path, new_name)
                        counter += 1

                    try:
                        # ✅ Check if old_path still exists before renaming
                        if not self.fileSystemService.exists(old_path):
                            logger.warning(f"Skipping rename: '{old_path}' does not exist.")
                            continue

                        self.fileSystemService.rename(old_path, new_path)
                        logger.info(f"Renamed '{movie}' -> '{new_name}'")

                    except ValueError as ve:
                        logger.error(f"Rename failed due to validation error: {ve}")
                    except OSError as e:
                        logger.error(f"Failed to rename '{movie}' to '{new_name}': {e}")

                pbar.update(1)  # ✅ Update progress bar

    def moving_to_vose(self) -> None:
        """
        Move genre folders from TEMP to VOSE directory, merging contents instead of replacing.
        If a folder already exists and has conflicting content (e.g., same movie folder, partial files), the process will stop with an error.
        """
        logger = logging.getLogger(__name__)
        print("\nSTEP::4 .... moving_to_vose")

        # ✅ Get TEMP and VOSE directories
        temp_path = self._get_temp_path(self.configService.getDirectorySource())
        vose_path = self.configService.getDirectoryTarget()  # ✅ Use correct getter method

        # ✅ Ensure VOSE directory exists
        self.fileSystemService.ensure_directory_exists(vose_path)

        # ✅ Get all genre folders inside TEMP
        genres = self.fileSystemService.get_folders_at(temp_path)
        logger.info(f"Found {len(genres)} genre folders in TEMP.")

        # ✅ Use tqdm progress bar
        with tqdm(total=len(genres), desc="Merging Genres", unit="folder") as pbar:
            for genre in genres:
                from_genre_path = self.fileSystemService.join(temp_path, genre)
                to_genre_path = self.fileSystemService.join(vose_path, genre)

                # ✅ Ensure genre folder exists in VOSE
                self.fileSystemService.ensure_directory_exists(to_genre_path)

                # ✅ Get movie folders in the current genre
                movies = self.fileSystemService.get_folders_at(from_genre_path)
                logger.info(f"Merging '{genre}' genre with {len(movies)} movies.")

                for movie in movies:
                    from_movie_path = self.fileSystemService.join(from_genre_path, movie)
                    to_movie_path = self.fileSystemService.join(to_genre_path, movie)

                    try:
                        self.fileSystemService.move(from_movie_path, to_movie_path, preserve_folder_name=False)
                        logger.info(f"✅ Successfully moved '{movie}' to '{to_movie_path}'.")
                    except RuntimeError as e:
                        logger.critical(f"❌ Merge conflict detected for '{movie}': {e}")
                        raise  # ⛔ Stop the entire process
                    except OSError as e:
                        logger.error(f"⚠️ Failed to move '{movie}' to VOSE: {e}")

                pbar.update(1)  # ✅ Update progress bar

    def deleting_temp(self) -> None:
        """
        Delete the TEMP directory after processing.
        """
        print("STEP::5 .... deleting_temp")
        temp_path = self._get_temp_path(self.configService.getDirectorySource())  # ✅ Correct

        try:
            self.fileSystemService.rmdir(temp_path)
        except OSError as e:
            print(f"Failed to delete TEMP directory: {e}")

    # Private helper methods
    def _prepare_temp_directory(self, temp_path: str) -> None:
        """
        Prepare the TEMP directory by ensuring it exists.

        Args:
            temp_path (str): Full path to the TEMP directory.
        """
        logger = logging.getLogger(__name__)
        logger.info(f" @_prepare_temp_directory before => TEMP_DIR_NAME = {self.TEMP_DIR_NAME}")
        print(f" @_prepare_temp_directory before => TEMP_DIR_NAME = {self.TEMP_DIR_NAME}")

        parent_path = os.path.dirname(temp_path)  # Get the parent directory

        # Ensure the TEMP directory exists and remove it if needed
        self.fileSystemService.cd(parent_path)  # ✅ Move to the parent directory
        
        try:
            if self.fileSystemService.get_folders().__contains__(self.TEMP_DIR_NAME):
                logger.info(f"Removing existing TEMP directory: {temp_path}")
                #self.fileSystemService.rmdir(self.TEMP_DIR_NAME)  # ✅ Remove TEMP directory if it exists
                print(f" @_prepare_temp_directory after remove => TEMP_DIR_NAME = {self.TEMP_DIR_NAME}")
        except OSError:
            pass  # Ignore errors if the directory doesn't exist

        logger.info(f"Creating TEMP directory: {temp_path}")
        self.fileSystemService.ensure_directory_exists(temp_path)  # ✅ Ensure TEMP exists
        self.fileSystemService.cd(temp_path)  # ✅ Navigate to TEMP
            
    def _get_temp_path(self, base_path: str) -> str:
        """
        Build the TEMP directory path at the same level as RAW.

        Args:
            base_path (str): The RAW directory path.

        Returns:
            str: Full absolute path to the TEMP directory.
        """
        raw_parent = os.path.dirname(base_path)  # ✅ Get the parent directory of RAW
        temp_path = self.fileSystemService.join(raw_parent, self.TEMP_DIR_NAME)  # ✅ Place TEMP next to RAW
        return os.path.abspath(temp_path)  # ✅ Ensure it's an absolute path
