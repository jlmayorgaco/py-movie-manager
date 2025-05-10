import unittest
from unittest.mock import MagicMock
import os
import shutil
from src.domain.classes.MovieManagerClass import MovieManager
from src.domain.classes.ConfigClass import Config


class TestMovieManager(unittest.TestCase):

    def setUp(self):
        self.sandbox_dir = os.path.abspath("tests/test_movie_manager__sandbox")
        self.raw_dir = os.path.join(self.sandbox_dir, "RAW")
        self.vose_dir = os.path.join(self.sandbox_dir, "VOSE")
        self.temp_dir = os.path.join(self.sandbox_dir, "__TMM_TEMP__")

        if os.path.exists(self.sandbox_dir):
            shutil.rmtree(self.sandbox_dir)

        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.vose_dir, exist_ok=True)

        self.mock_file_system = MagicMock()
        self.mock_filter_service = MagicMock()
        self.mock_scrapper_service = MagicMock()

        self.mock_config_service = Config()
        self.mock_config_service.directory_raw = self.raw_dir
        self.mock_config_service.directory_vose = self.vose_dir
        self.mock_config_service.genres = ["Action", "Comedy", "Drama"]

        self.mock_file_system.join.side_effect = os.path.join

        self.manager = MovieManager()
        self.manager.setServiceConfig(self.mock_config_service)
        self.manager.setServiceFileSystem(self.mock_file_system)
        self.manager.setServiceFilter(self.mock_filter_service)
        self.manager.setServiceScrapper(self.mock_scrapper_service)

    def tearDown(self):
        if os.path.exists(self.sandbox_dir):
            shutil.rmtree(self.sandbox_dir)

    def test_start(self):
        self.manager.start()
        self.mock_file_system.cd.assert_any_call(self.raw_dir)
        self.mock_file_system.rmdir.assert_called_with(self.temp_dir)
        self.mock_file_system.mkdir.assert_called_with(self.temp_dir)
        self.mock_file_system.cd.assert_called_with(self.temp_dir)

    def test_creating_temp_genres(self):
        self.manager.creating_temp_genres()
        self.mock_file_system.cd.assert_called_with(self.temp_dir)
        for genre in self.mock_config_service.genres:
            self.mock_file_system.mkdir.assert_any_call(genre)

    def test_moving_to_temp(self):
        folders = ["Movie1 [g-Action]", "Movie2 [g-Comedy]", "Movie3 [g-Drama]"]
        self.mock_file_system.get_folders.return_value = folders
        self.mock_filter_service.getGenreByFolderName.side_effect = ["Action", "Comedy", "Drama"]
        self.mock_filter_service.getGenreByMostLikehood.side_effect = ["Action", "Comedy", "Drama"]

        self.manager.moving_to_temp()
        for folder, genre in zip(folders, self.mock_config_service.genres):
            from_path = os.path.join(self.raw_dir, folder)
            to_path = os.path.join(self.temp_dir, genre)
            self.mock_file_system.move.assert_any_call(from_path, to_path)

    def test_renaming_in_temp(self):
        genre_folders = ["Action", "Comedy"]
        movie_folders_action = ["Movie1 [g-Action]"]
        movie_folders_comedy = ["Movie2 [g-Comedy]"]

        self.mock_file_system.get_folders.side_effect = [
            genre_folders,
            movie_folders_action,
            movie_folders_comedy,
        ]
        self.mock_filter_service.clean.side_effect = ["Movie1", "Movie2"]

        self.manager.renaming_in_temp()
        self.mock_file_system.cd.assert_any_call(self.temp_dir)

        for genre in genre_folders:
            self.mock_file_system.cd.assert_any_call(genre)

        self.mock_file_system.rename.assert_any_call("Movie1 [g-Action]", "Movie1")
        self.mock_file_system.rename.assert_any_call("Movie2 [g-Comedy]", "Movie2")

    def test_moving_to_vose(self):
        genre_folders = ["Action", "Comedy"]
        self.mock_file_system.get_folders.return_value = genre_folders

        self.manager.moving_to_vose()
        for genre in genre_folders:
            from_path = os.path.join(self.temp_dir, genre)
            to_path = self.vose_dir
            self.mock_file_system.move.assert_any_call(from_path, to_path)

    def test_deleting_temp(self):
        self.manager.deleting_temp()
        self.mock_file_system.rmdir.assert_called_with(self.temp_dir)

    def test_prepare_temp_directory(self):
        self.manager._prepare_temp_directory(self.temp_dir)
        self.mock_file_system.rmdir.assert_called_with(self.temp_dir)
        self.mock_file_system.mkdir.assert_called_with(self.temp_dir)
        self.mock_file_system.cd.assert_called_with(self.temp_dir)

    def test_get_temp_path(self):
        temp_path = self.manager._get_temp_path(self.raw_dir)
        self.assertEqual(temp_path, os.path.join(self.sandbox_dir, "__TMM_TEMP__"))


if __name__ == "__main__":
    unittest.main()
