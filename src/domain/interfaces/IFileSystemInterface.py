from abc import abstractmethod
from abc import ABCMeta
from ..interfaces.IFilterServiceInterface import IFilterService
from ..interfaces.IConfigInterface import IConfig

class IFileSystem(metaclass=ABCMeta):

    @abstractmethod
    def cd(path: str):
        pass

    @abstractmethod
    def back(path: str):
        pass

    @abstractmethod
    def setConfig(config: IConfig) -> None:
        pass

    @abstractmethod
    def getConfig() -> IConfig:
        pass

    @abstractmethod
    def setFilter(service: IFilterService) -> None:
        pass

    @abstractmethod
    def getFilter() -> IFilterService:
        pass

    @abstractmethod
    def get_folder(folder_name: str) -> str:
        pass

    @abstractmethod
    def create_folder(folder_name: str)-> int:
        pass

    @abstractmethod
    def move_folder(origin_path, destination_path: str) -> int:
        pass

    @abstractmethod
    def delete_folder(folder_name: str) -> int:
        pass

    @abstractmethod
    def get_folders() -> list[str]:
        pass

    @abstractmethod
    def create_folders() -> int:
        pass

    @abstractmethod
    def move_folders() -> int:
        pass

    @abstractmethod
    def delete_folders() -> int:
        pass