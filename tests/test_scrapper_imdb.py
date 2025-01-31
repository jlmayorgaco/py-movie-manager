import unittest
from src.domain.classes.ScrapperServiceIMDB import ScrapperServiceIMDB


class TestScrapperServiceIMDB(unittest.TestCase):

    def setUp(self):
        self.scrapper = ScrapperServiceIMDB()
        self.scrapper.setApiKey("mock_api_key")

    def test_setApiKey_valid(self):
        """
        Test setting a valid API key.
        """
        self.scrapper.setApiKey("new_api_key")
        self.assertEqual(self.scrapper.apiKey, "new_api_key")

    def test_setApiKey_invalid(self):
        """
        Test setting an invalid API key raises a ValueError.
        """
        with self.assertRaises(ValueError):
            self.scrapper.setApiKey("")

    def test_getMovieByNameAndYear_valid(self):
        """
        Test fetching movie details with valid input.
        """
        movie = self.scrapper.getMovieByNameAndYear("Inception", 2010)
        self.assertIsNotNone(movie)
        self.assertEqual(movie["name"], "Inception")
        self.assertEqual(movie["year"], 2010)

    def test_getMovieByNameAndYear_noApiKey(self):
        """
        Test calling getMovieByNameAndYear without an API key raises ValueError.
        """
        scrapper = ScrapperServiceIMDB()
        with self.assertRaises(ValueError):
            scrapper.getMovieByNameAndYear("Inception", 2010)

    def test_getMovieByNameAndYear_invalidName(self):
        """
        Test calling getMovieByNameAndYear with invalid movie name raises ValueError.
        """
        with self.assertRaises(ValueError):
            self.scrapper.getMovieByNameAndYear("", 2010)

    def test_getMovieByNameAndYear_invalidYear(self):
        """
        Test calling getMovieByNameAndYear with invalid year raises ValueError.
        """
        with self.assertRaises(ValueError):
            self.scrapper.getMovieByNameAndYear("Inception", -2010)


if __name__ == "__main__":
    unittest.main()
