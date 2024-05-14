import re
from Levenshtein import distance

from ..interfaces.IFilterServiceInterface import IFilterService

class FilterServiceDefault(IFilterService):
    def __init__(self):
        self.search_genre_tag = ''
        self.search_director_tag = ''
        self.genres = []

    def __str__(self):
        return f''' 
        FilterServiceDefault::search_genre_tag <{self.search_genre_tag}>
        FilterServiceDefault::search_director_tag <{self.search_director_tag}>
        '''
    def setGenres(self, genres: list[str]):
        self.genres = genres
    
    def setGenreSearchTag(self, tag: str):
        self.search_genre_tag = tag

    def setDirectorSearchTag(self, tag: str):
         self.search_director_tag = tag

    def getGenreByMostLikehood(self, genre):
        # Find the most similar genre folder
        genres_folders = self.genres
        most_similar_folder = min(genres_folders, key=lambda x: distance(x.upper(), genre.upper()))
        return most_similar_folder

    def clean(self, folder_string):
        # Define the regular expression pattern to match [g-...][d-...] at the beginning of the string
        pattern = re.compile(r'^\[g-(.*?)\]\[d-(.*?)\]')
        # Use re.sub to replace the matched pattern with an empty string
        cleaned_folder = re.sub(pattern, '', folder_string)
        # Strip any leading or trailing spaces
        cleaned_folder = cleaned_folder.strip()
        return cleaned_folder

    def getGenreByFolderName(self, foldername: str):
         # fill this class method
         # Use regular expression to extract the genre from the folder name
        match = re.search(r'\[g-(.*?)\]', foldername)

        # Check if a match is found
        if match:
            genre = match.group(1)
            return genre
        else:
            return "Unknown"