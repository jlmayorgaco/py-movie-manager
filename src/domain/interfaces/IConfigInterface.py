from abc import abstractmethod
from abc import ABCMeta

class IConfig(metaclass=ABCMeta):

    def __init__(self):
        pass

    @abstractmethod
    def setDirectorySource(path):
        pass

    @abstractmethod
    def setDirectoryTarget(path):
        pass

    @abstractmethod
    def setGenres(self, genres):
        pass

    @abstractmethod
    def is_preflight(self) -> bool: pass
    @abstractmethod
    def set_preflight(self, preflight: bool): pass

    @abstractmethod
    def is_plan(self) -> bool: pass
    @abstractmethod
    def set_plan(self, plan: bool): pass

    @abstractmethod
    def is_resume(self) -> bool: pass
    @abstractmethod
    def set_resume(self, resume: bool): pass

    @abstractmethod
    def get_limit(self) -> int: pass
    @abstractmethod
    def set_limit(self, limit: int): pass

    @abstractmethod
    def get_log_level(self) -> str: pass
    @abstractmethod
    def set_log_level(self, level: str): pass

    @abstractmethod
    def get_report_dir(self) -> str: pass
    @abstractmethod
    def set_report_dir(self, report_dir: str): pass

    @abstractmethod
    def get_workers(self) -> int: pass
    @abstractmethod
    def set_workers(self, workers: int): pass

    @abstractmethod
    def get_stop_on_conflict(self) -> bool: pass
    @abstractmethod
    def set_stop_on_conflict(self, stop: bool): pass

    @abstractmethod
    def get_continue_on_error(self) -> bool: pass
    @abstractmethod
    def set_continue_on_error(self, cont: bool): pass

    @abstractmethod
    def get_sort(self) -> str: pass
    @abstractmethod
    def set_sort(self, sort: str): pass
