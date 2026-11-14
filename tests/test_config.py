import tempfile
import unittest
from pathlib import Path

from config.GenresConfig import GenresEnum
from src.domain.classes.ConfigClass import Config


class TestConfig(unittest.TestCase):
    def setUp(self):
        """
        Set up a Config instance for testing.
        """
        fixture = tempfile.TemporaryDirectory()
        self.addCleanup(fixture.cleanup)
        config_path = Path(fixture.name) / "config.json"
        config_path.write_text("{}", encoding="utf-8")
        self.config = Config(str(config_path))

    def test_initial_state(self):
        """
        Test that the Config class initializes with default values.
        """
        self.assertEqual(self.config.getDirectorySource(), "")
        self.assertEqual(self.config.getDirectoryTarget(), "")
        self.assertEqual(self.config.getGenres(), [])

    def test_set_directory_source_valid(self):
        """
        Test setting a valid source directory.
        """
        self.config.setDirectorySource("/source/path")
        self.assertEqual(self.config.getDirectorySource(), "/source/path")

    def test_set_directory_source_invalid(self):
        """
        Test setting an invalid (empty) source directory.
        """
        with self.assertRaises(ValueError):
            self.config.setDirectorySource("")

    def test_set_directory_target_valid(self):
        """
        Test setting a valid target directory.
        """
        self.config.setDirectoryTarget("/target/path")
        self.assertEqual(self.config.getDirectoryTarget(), "/target/path")

    def test_set_directory_target_invalid(self):
        """
        Test setting an invalid (empty) target directory.
        """
        with self.assertRaises(ValueError):
            self.config.setDirectoryTarget("")

    def test_set_genres_valid(self):
        """
        Test setting valid genres.
        """
        genres = [GenresEnum.ACTION, GenresEnum.COMEDY, GenresEnum.DRAMA]
        self.config.setGenres(genres)
        self.assertEqual(self.config.getGenres(), ["ACTION", "COMEDY", "DRAMA"])

    def test_set_genres_invalid(self):
        """
        Test setting invalid genres (non-GenresEnum values).
        """
        with self.assertRaises(ValueError):
            self.config.setGenres(["InvalidGenre"])

    def test_string_representation(self):
        """
        Test the string representation of the Config object.
        """
        self.config.setDirectorySource("/source/path")
        self.config.setDirectoryTarget("/target/path")
        genres = [GenresEnum.ACTION, GenresEnum.COMEDY]
        self.config.setGenres(genres)

        for line in (
            "Config::Directory Source </source/path>",
            "Config::Directory Target </target/path>",
            "Config::Genres <ACTION, COMEDY>",
        ):
            self.assertIn(line, str(self.config).splitlines())


if __name__ == "__main__":
    unittest.main()
