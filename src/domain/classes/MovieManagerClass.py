from enum import Enum

from ..interfaces.IMovieManagerInterface import IMovieManager
from ..classes.ConfigClass import Config

class MovieManager(IMovieManager):

    def __init__(self):
        self.configService = None
        self.scrapperService = None
        self.filterService = None
        self.fileSystemService = None

    def __str__(self):
        return f'''
        MovieManager::ConfigService <{self.configService}>

        MovieManager::ScrapperService <{self.scrapperService}>

        MovieManager::FilterService <{self.filterService}>

        MovieManager::FileSystemService <{self.fileSystemService}>
        '''

    def setServiceConfig(self, configService: Config):
        self.configService = configService
        return 1

    def setServiceFilter(self, filterService):
        self.filterService = filterService
        return 1

    def setServiceFileSystem(self, filesystemService):
        self.fileSystemService = filesystemService
        return 1

    def setServiceScrapper(self, scrapperService):
        self.scrapperService = scrapperService
        return 1

    def start(self):

        # Movin to RAW directory
        temp_dir = '__TMM_TEMP__'
        path_raw = self.configService.directory_raw
        path_vose = self.configService.directory_vose
        path_temp = path_raw + '/../' + temp_dir
        self.fileSystemService.cd(path_raw)

        # Creating TEMP folder
        self.fileSystemService.cd('..')

        #self.fileSystemService.rmdir(temp_dir)
        #print(' __TEMP__ Deleted')
    
        #self.fileSystemService.mkdir(temp_dir)
        #print(' __TEMP__ Created')

        self.fileSystemService.cd(temp_dir)
        print(' cd to __TEMP__')
        return 1
    def creating_temp_genres(self):

        print(' STEP::1 .... creating_temp ')

        temp_dir = '__TMM_TEMP__'
        path_raw = self.configService.directory_raw
        path_vose = self.configService.directory_vose
        path_temp = path_raw + '/../' + temp_dir

        # Go to Temp Directory
        self.fileSystemService.cd(path_temp)

        # Creating Genre Folders in TEMP
        genres = self.configService.getGenres()
        try:
            for genre in genres:
                self.fileSystemService.mkdir(genre)  # Creating the directory
                #print(f"Created directory for genre '{genre}' at '{temp_dir}'")
        except OSError as e:
            print(f"Failed to create genre directories: {e}")

        # Go Again to RAW Directory
        self.fileSystemService.cd(path_raw)
           # Go Again to RAW Directory
        self.fileSystemService.cd(path_raw)

        return 1
    def moving_to_temp(self):

        print(' STEP::2 .... moving_to_temp ')


        temp_dir = '__TMM_TEMP__'
        path_raw = self.configService.directory_raw
        path_vose = self.configService.directory_vose
        path_temp = path_raw + '/../' + temp_dir

        # Loop over each folder and move to to respective genre
        print(' .. Moving to ___TEMP___ ') 
        folders = self.fileSystemService.get_folders()
        try:
            for folder in folders:

                # Move to Genre Folder
                genre_by_folder = self.filterService.getGenreByFolderName(folder)
                gender_by_most_likehood = self.filterService.getGenreByMostLikehood(genre_by_folder)
                from_path = self.fileSystemService.join(path_raw, folder)
                to_path = self.fileSystemService.join(path_temp,gender_by_most_likehood)
                self.fileSystemService.move(from_path, to_path)

        except OSError as e:
            print(f"Failed to moves moves to genre directories: {e}")
    def renaming_in_temp(self):

        print(' STEP::3 .... renaming_in_temp ')

        temp_dir = '__TMM_TEMP__'
        path_raw = self.configService.directory_raw
        path_vose = self.configService.directory_vose
        path_temp = path_raw + '/../' + temp_dir

        # Move fron Genre Folder to VOSE Folders 1412 164 = 
        print(' .. Cleaning Names ')
        self.fileSystemService.cd(path_temp)
        genre_folders = self.fileSystemService.get_folders()
        try:
            for genre_folder in genre_folders:
                self.fileSystemService.cd(genre_folder)
                self.fileSystemService.rmdir('.deletedByTMM')
                movies = self.fileSystemService.get_folders()
                for movie in movies:
                    prev_movie_name = movie
                    new_movie_name = self.filterService.clean(movie)
                    self.fileSystemService.rename(prev_movie_name, new_movie_name)

                # Go Back to __TEMP__
                self.fileSystemService.cd('..')
        except OSError as e:
            print(f"Failed to moves moves to genre directories: {e}")
    def moving_to_vose(self):

        print(' STEP::4 .... moving_to_vose ')

        temp_dir = '__TMM_TEMP__'
        path_raw = self.configService.directory_raw
        path_vose = self.configService.directory_vose
        path_temp = path_raw + '/../' + temp_dir

         # Move Genres to VOSE
        genre_folders = self.fileSystemService.get_folders()
        for genre_folder in genre_folders:
            from_path = self.fileSystemService.join(path_temp, genre_folder)
            to_path = self.fileSystemService.join(path_vose, '')
            self.fileSystemService.move2(from_path, to_path)

    def deleting_temp(self):
        print(' STEP::5 .... deleting_temp ')
