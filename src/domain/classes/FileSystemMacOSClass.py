import os
import shutil

from ..interfaces.IFileSystemInterface import IFileSystem

class FileSystemMacOS(IFileSystem):
    def __init__(self):
        self.cwd = ''
        self.filterService = None

    def __str__(self):
        return f'''
        FileSystemMacOS::CWD <{self.cwd}>
        '''

    def cd(self, path: str):
        try:
            os.chdir(path)
            print(f''' ... cd to <{os.getcwd()}>''')
            print(f''' ''')
        except OSError:
            print("Failed to change directory. Directory may not exist or access denied.")

    def rename(self, folder: str, new_name: str) -> bool:
        try:
            # Get the full path of the folder
            current_path = os.path.join(os.getcwd(), folder)
            # Construct the new path with the new name
            new_path = os.path.join(os.getcwd(), new_name)
            # Rename the folder
            os.rename(current_path, new_path)
            print(f"Renamed folder '{folder}' to '{new_name}' successfully.")
            return True
        except OSError as e:
            print(f"Failed to rename folder '{folder}' to '{new_name}': {e}")
            return False

    def mkdir(self, folder_name: str):
        try:
            os.mkdir(folder_name)
            directories = [name for name in os.listdir() if os.path.isdir(name)]
            #print(" ... Other folders in the current directory:")
            #for directory in directories:
                #print('          => ' + directory)
        except OSError:
            print(f"Creation of the folder '{folder_name}' failed.")
    def rmdir(self, folder_name: str):
        try:
            shutil.rmtree(os.path.join(os.getcwd(), folder_name))

            #print(f" ... rm -r in folder '{folder_name}' deleted successfully.")
        except OSError:
            print(f"Deletion of the folder '{folder_name}' failed.")

    def join(self, path, folder):
        return os.path.join(path, folder)

    def back(self, path: str):
        return 1

    def move(self, from_path: str, to_path: str) -> bool:
        try:
            # Check if the destination directory exists
            if os.path.exists(os.path.join(to_path, os.path.basename(from_path))):
                # Remove the destination directory
                print('Folder already exist')
                print(os.path.join(to_path, os.path.basename(from_path)))
                #shutil.rmtree(os.path.join(to_path, os.path.basename(from_path)))

            # Define a custom copy function to overwrite existing files
            def copy_with_overwrite_func(src, dst, *, follow_symlinks=True):
                shutil.copy2(src, dst, follow_symlinks=follow_symlinks)

            # Copy the entire directory tree from 'from_path' to 'to_path'
            shutil.copytree(from_path, os.path.join(to_path, os.path.basename(from_path)), copy_function=copy_with_overwrite_func)

            # Remove the original directory tree
            shutil.rmtree(from_path)

            print(f''' 
                  Moved '{from_path}' 
                  To '{to_path}' successfully.

            ''')
            return os.path.join(to_path, os.path.basename(from_path))
        except OSError as e:
            print(f"Failed to move '{from_path}' to '{to_path}': {e}")
            return False


    def move2(self, from_path: str, to_path: str) -> bool:
        try:

            # Define a custom copy function to overwrite existing files
            def copy_with_overwrite_func(src, dst, *, follow_symlinks=True):
                shutil.copy2(src, dst, follow_symlinks=follow_symlinks)

            # Copy the entire directory tree from 'from_path' to 'to_path'
            shutil.copytree(from_path, os.path.join(to_path, os.path.basename(from_path)), copy_function=copy_with_overwrite_func)

            # Remove the original directory tree
            shutil.rmtree(from_path)

            print(f''' 
                  Moved '{from_path}' 
                  To '{to_path}' successfully.

            ''')
            return os.path.join(to_path, os.path.basename(from_path))
        except OSError as e:
            print(f"Failed to move '{from_path}' to '{to_path}': {e}")
            return False

    def setFilter(self, filterService):
        self.filterService = filterService

    def getFilter(self):
        return self.filterService

    def setConfig(self, configService):
        self.configService = configService

    def getConfig(self):
        return self.configService

    def hasFilter(self):
        return (self.getFilter() is not None)


    def get_folder(folder_name):
        return folder_name

    def create_folder(folder_name):
        return 1

    def move_folder(origin_path, destination_path):
        return 1

    def delete_folder(folder_name):
        return 1

    def get_folders(self):
        try:
            folders = [name for name in os.listdir() if os.path.isdir(name)]
            return folders
        except OSError:
            print("Failed to get folders in the current directory.")
            return []

    def create_folders():
        return 1

    def move_folders():
        return 1

    def delete_folders():
        return 1

