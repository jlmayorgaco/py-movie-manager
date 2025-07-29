from typing import Optional, Dict
from src.domain.interfaces.IScrapperInterface import IScrapper


class ScrapperServiceIMDB(IScrapper):
    """
    ScrapperServiceIMDB: A service for interacting with the IMDb API to fetch movie data.
    """

    def __init__(self):
        """
        Initialize the ScrapperServiceIMDB with default values.
        """
        self.apiKey: Optional[str] = None

    def __str__(self) -> str:
        """
        String representation of the current API key configuration.

        Returns:
            str: A string containing the API key.
        """
        return f"ScrapperServiceIMDB::apiKey <{self.apiKey}>"

    def setApiKey(self, apikey: str) -> None:
        """
        Set the API key for IMDb API access.

        Args:
            apikey (str): The API key for authenticating requests.
        """
        if not apikey or not isinstance(apikey, str):
            raise ValueError("API key must be a non-empty string.")
        self.apiKey = apikey

    def getMovieByNameAndYear(self, name: str, year: int) -> Optional[Dict]:
        """
        Fetch movie details from IMDb by name and release year.

        Args:
            name (str): The name of the movie.
            year (int): The release year of the movie.

        Returns:
            Optional[Dict]: Movie details as a dictionary if found, otherwise None.
        """
        if not self.apiKey:
            raise ValueError("API key is not set. Use `setApiKey` to configure the API key.")

        if not name or not isinstance(name, str):
            raise ValueError("Movie name must be a non-empty string.")

        if not isinstance(year, int) or year <= 0:
            raise ValueError("Year must be a positive integer.")

        # Simulated API request (replace with real API integration)
        response = self._mockApiCall(name, year)

        if response:
            return response
        else:
            return None

    def _mockApiCall(self, name: str, year: int) -> Optional[Dict]:
        """
        Mock API call to simulate IMDb data fetching (for testing purposes).

        Args:
            name (str): The name of the movie.
            year (int): The release year of the movie.

        Returns:
            Optional[Dict]: Simulated movie details or None.
        """
        # Simulate a response for testing
        mock_data = {
            "name": name,
            "year": year,
            "director": "John Doe",
            "genre": ["Drama", "Thriller"],
            "rating": 8.5,
        }
        return mock_data
