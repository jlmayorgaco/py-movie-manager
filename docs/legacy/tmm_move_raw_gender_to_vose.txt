#!/usr/bin/env python3

import os
from libs.get_movies_in_raw import get_movies_raw_folders
from libs.get_movies_in_raw import get_genre_from_folder
from libs.get_movies_in_raw import get_genres_raw_folders
from libs.get_movies_in_raw import move_folders_to_genres
from libs.get_movies_in_raw import remove_deleted_by_tmm_folders
from libs.get_movies_in_raw import rename_dirs_and_files
from libs.get_movies_in_raw import move_folders_to_vose_genres

# Config Variables
dir_raw_genres = "/Volumes/DX517/Movies/[Movies] Filmoteca/[Movies] Filmoteca VOSE RAW/"
dir_raw_raw = "/Volumes/DX517/Movies/[Movies] Filmoteca/[Movies] Filmoteca VOSE RAW/RAW"


# Global Variables
folders_genres = get_genres_raw_folders(dir_raw_genres)
folders_movies_in_raw = get_movies_raw_folders(dir_raw_raw)

# Move movies from RAW to its Raw Genres Folders
move_folders_to_genres(folders_movies_in_raw, folders_genres)

# Delete All .deletedByTMM directories
remove_deleted_by_tmm_folders(dir_raw_genres)

# Rename Dir and Files in Raw Genres dir_raw_genres subfolders
rename_dirs_and_files(dir_raw_genres)

# Move from Raw Genres to VOSE Genres
move_folders_to_vose_genres(dir_raw_genres)