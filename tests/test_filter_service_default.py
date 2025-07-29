import unittest
from src.domain.classes.FilterServiceDefaultClass import FilterServiceDefault


class TestFilterServiceDefault(unittest.TestCase):

    def setUp(self):
        self.filter_service = FilterServiceDefault()
        self.filter_service.setGenres(["Action", "Comedy", "Drama", "Thriller"])
        self.filter_service.setGenreSearchTag("[g-*]")
        self.filter_service.setDirectorSearchTag("[d-*]")

    def test_getGenreByMostLikelihood(self):
        genre = "Thriler"
        most_likely = self.filter_service.getGenreByMostLikelihood(genre)
        self.assertEqual(most_likely, "Thriller")

    def test_clean(self):
        folder_name = "[g-Action][d-Spielberg] Movie Name"
        cleaned_name = self.filter_service.clean(folder_name)
        self.assertEqual(cleaned_name, "Movie Name")

    def test_getGenreByFolderName(self):
        folder_name = "[g-Drama] A Great Movie"
        genre = self.filter_service.getGenreByFolderName(folder_name)
        self.assertEqual(genre, "Drama")

    def test_getGenreByFolderName_unknown(self):
        folder_name = "A Movie Without Tags"
        genre = self.filter_service.getGenreByFolderName(folder_name)
        self.assertEqual(genre, "Unknown")

    def test_extractTags(self):
        folder_name = "[g-Comedy][d-Tarantino] A Funny Movie"
        tags = self.filter_service.extractTags(folder_name)
        self.assertEqual(tags, {'genre': "Comedy", 'director': "Tarantino"})

    def test_extractTags_unknown(self):
        folder_name = "Untitled"
        tags = self.filter_service.extractTags(folder_name)
        self.assertEqual(tags, {'genre': "Unknown", 'director': "Unknown"})


if __name__ == "__main__":
    unittest.main()
