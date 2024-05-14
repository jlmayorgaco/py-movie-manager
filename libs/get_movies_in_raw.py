import os
import re
import shutil
from shutil import move
from Levenshtein import distance

# Config Variables
dir_vose_genres = "/Volumes/DX517/Movies/[Movies] Filmoteca/[Movies] Filmoteca VOSE/"
dir_raw_genres = "/Volumes/DX517/Movies/[Movies] Filmoteca/[Movies] Filmoteca VOSE RAW/"
dir_raw_raw = "/Volumes/DX517/Movies/[Movies] Filmoteca/[Movies] Filmoteca VOSE RAW/RAW"

def get_genre_from_folder(folder_name):
    # Use regular expression to extract the genre from the folder name
    match = re.search(r'\[g-(.*?)\]', folder_name)

    # Check if a match is found
    if match:
        genre = match.group(1)
        return genre
    else:
        return "Unknown"
def get_genres_raw_folders(directory):
    folders = []

    # Get Movies from RAW Folder
    if os.path.isdir(directory):
        os.chdir(directory)

        # Use os.listdir to get all folders inside the specified directory
        folders = [item for item in os.listdir() if os.path.isdir(item) and "RAW" not in item]

    else:
        print(f"Directory {directory} does not exist.")

    return folders

def get_movies_raw_folders(directory):
    folders = []

    # Get Movies from RAW Folder
    if os.path.isdir(directory):
        os.chdir(directory)

        # Use os.listdir to get all folders inside the specified directory
        folders = [item for item in os.listdir() if os.path.isdir(item) and "RAW" not in item]

    else:
        print(f"Directory {directory} does not exist.")

    # Create a list of dictionaries
    objects_list = [{'genre': get_genre_from_folder(folder), 'directory': folder} for folder in folders]

    return objects_list

def move_folders_to_genres(folders_movies, genres_folders):
    for movie_folder in folders_movies:
        genre = movie_folder['genre']
        most_similar_genre_folder = find_most_similar_genre_folder(genre, genres_folders)

        if movie_folder['genre'] and most_similar_genre_folder:
            source_path = os.path.join(dir_raw_raw, movie_folder['directory'])
            destination_path = os.path.join(dir_raw_genres, most_similar_genre_folder)

            # Move the folder to the destination
            if (os.path.exists(destination_path)):
                shutil.rmtree(source_path)
            else:
                move(source_path, destination_path)
                print(f"Moved folder '{movie_folder}' to '{most_similar_genre_folder}' genre.")


def find_most_similar_genre_folder(genre, genres_folders):
    # Find the most similar genre folder
    most_similar_folder = min(genres_folders, key=lambda x: distance(x.lower(), genre.lower()))
    return most_similar_folder

def remove_deleted_by_tmm_folders(root_directory):
    for dirpath, dirnames, filenames in os.walk(root_directory, topdown=False):
        for dirname in dirnames:
            if dirname == ".deletedByTMM":
                folder_path = os.path.join(dirpath, dirname)
                print(f"Removing folder: {folder_path}")
                shutil.rmtree(folder_path)

def remove_genre_director(folder_string):
    # Define the regular expression pattern to match [g-...][d-...] at the beginning of the string
    pattern = re.compile(r'^\[g-(.*?)\]\[d-(.*?)\]')
    # Use re.sub to replace the matched pattern with an empty string
    cleaned_folder = re.sub(pattern, '', folder_string)
    # Strip any leading or trailing spaces
    cleaned_folder = cleaned_folder.strip()
    return cleaned_folder

def rename_dirs_and_files(root_directory):
    for root, dirs, files in os.walk(root_directory):
        for directory in dirs:

            if(dirs == 'RAW'):
                continue

            # Rename directories
            old_dir_path = os.path.join(root, directory)
            new_dir_name = modify_directory_name(directory)
            new_dir_path = os.path.join(root, new_dir_name)

            if old_dir_path != new_dir_path:
                os.rename(old_dir_path, new_dir_path)
                print(f"Renamed directory: {old_dir_path} to {new_dir_path}")

        for file in files:
            # Rename files
            old_file_path = os.path.join(root, file)
            new_file_name = modify_file_name(file)
            new_file_path = os.path.join(root, new_file_name)

            if old_file_path != new_file_path:
                os.rename(old_file_path, new_file_path)
                print(f"Renamed file: {old_file_path} to {new_file_path}")

def move_folders_to_vose_genres(raw_genres_directory):
    # List all items (files and directories) directly in the specified directory
    items = os.listdir(raw_genres_directory)

    for item in items:
        item_path = os.path.join(raw_genres_directory, item)

        # Check if the item is a directory and not named 'RAW'
        if os.path.isdir(item_path) and item != 'RAW':
            old_dir_path = item_path
            new_dir_path = os.path.join(dir_vose_genres, item)

            # Ensure the destination directory exists
            os.makedirs(new_dir_path, exist_ok=True)

            # Move all the contents from old_dir_path to new_dir_path
            for content_item in os.listdir(old_dir_path):
                content_item_path = os.path.join(old_dir_path, content_item)
                new_content_item_path = os.path.join(new_dir_path, content_item)
                shutil.move(content_item_path, new_content_item_path)

            # Remove the now-empty old_dir_path
            os.rmdir(old_dir_path)

            print(f"Moved contents from {old_dir_path} to {new_dir_path}")

def modify_directory_name(directory_name):
    # Remove content between [g-*] and [d-*]
    modified_name = re.sub(r'\[g-.*?\]', '', directory_name)
    modified_name = re.sub(r'\[d-.*?\]', '', modified_name)
    return modified_name.strip()

def modify_file_name(file_name):
    modified_name = re.sub(r'\[g-.*?\]', '', file_name)
    modified_name = re.sub(r'\[d-.*?\]', '', modified_name)
    return modified_name.strip()