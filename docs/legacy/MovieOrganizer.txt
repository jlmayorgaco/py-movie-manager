#!/usr/bin/env python3

import os
from libs.get_movies_in_raw import (get_movies_raw_folders,
                                     get_genres_raw_folders,
                                     move_folders_to_genres,
                                     remove_deleted_by_tmm_folders,
                                     rename_dirs_and_files,
                                     move_folders_to_vose_genres)

class MovieOrganizer:
    def __init__(self, raw_genres_dir, raw_raw_dir):
        self.raw_genres_dir = raw_genres_dir
        self.raw_raw_dir = raw_raw_dir

    def organize(self):
        genres_folders = self.get_genres_folders()
        movies_folders = self.get_movies_folders()

        self.move_movies_to_genres(movies_folders, genres_folders)
        self.remove_deleted_folders()
        self.rename_folders_and_files()
        self.move_to_vose_genres()

    def get_genres_folders(self):
        return get_genres_raw_folders(self.raw_genres_dir)

    def get_movies_folders(self):
        return get_movies_raw_folders(self.raw_raw_dir)

    def move_movies_to_genres(self, movies_folders, genres_folders):
        move_folders_to_genres(movies_folders, genres_folders)

    def remove_deleted_folders(self):
        remove_deleted_by_tmm_folders(self.raw_genres_dir)

    def rename_folders_and_files(self):
        rename_dirs_and_files(self.raw_genres_dir)

    def move_to_vose_genres(self):
        move_folders_to_vose_genres(self.raw_genres_dir)

if __name__ == "__main__":
    RAW_GENRES_DIR = "/Volumes/DX517/Movies/[Movies] Filmoteca/[Movies] Filmoteca VOSE RAW/"
    RAW_RAW_DIR = "/Volumes/DX517/Movies/[Movies] Filmoteca/[Movies] Filmoteca VOSE RAW/RAW"

    organizer = MovieOrganizer(RAW_GENRES_DIR, RAW_RAW_DIR)
    organizer.organize()
