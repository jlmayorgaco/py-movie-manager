from abc import abstractmethod, ABCMeta
from typing import List
from ..interfaces.IFilterServiceInterface import IFilterService
from ..interfaces.IConfigInterface import IConfig

class IFileSystem(metaclass=ABCMeta):

    @abstractmethod
    def cd(self, path: str):
        pass

    @abstractmethod
    def back(self) -> str:
        pass

    @abstractmethod
    def setConfig(self, config: IConfig) -> None:
        pass

    @abstractmethod
    def getConfig(self) -> IConfig:
        pass

    @abstractmethod
    def setFilter(self, service: IFilterService) -> None:
        pass

    @abstractmethod
    def getFilter(self) -> IFilterService:
        pass

    @abstractmethod
    def get_folder(self, folder_name: str) -> str:
        pass

    @abstractmethod
    def create_folder(self, folder_name: str) -> int:
        pass

    @abstractmethod
    def move_folder(self, origin_path: str, destination_path: str) -> int:
        pass

    @abstractmethod
    def delete_folder(self, folder_name: str) -> int:
        pass

    @abstractmethod
    def get_folders(self) -> List[str]:
        pass

    @abstractmethod
    def create_folders(self, folders: List[str]) -> int:
        pass

    @abstractmethod
    def move_folders(self, folders: List[str], destination_path: str) -> int:
        pass

    @abstractmethod
    def delete_folders(self, folders: List[str]) -> int:
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        pass

    @abstractmethod
    def is_file(self, path: str) -> bool:
        pass

    @abstractmethod
    def is_dir(self, path: str) -> bool:
        pass

    @abstractmethod
    def get_size(self, path: str) -> int:
        pass

    @abstractmethod
    def copy_file(self, src: str, dst: str) -> None:
        pass

    @abstractmethod
    def remove_file(self, path: str) -> None:
        pass

    @abstractmethod
    def remove_directory(self, path: str) -> None:
        pass

    @abstractmethod
    def ensure_directory_exists(self, path: str) -> None:
        pass

    @abstractmethod
    def get_folders_at(self, path: str) -> List[str]:
        pass

    @abstractmethod
    def get_files_at(self, path: str) -> List[str]:
        pass

    @abstractmethod
    def rename(self, old_path: str, new_path: str) -> None:
        pass

    @abstractmethod
    def move(self, from_path: str, to_path: str) -> None:
        pass

    @abstractmethod
    def join(self, *paths: str) -> str:
        pass
