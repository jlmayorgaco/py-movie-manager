from __future__ import annotations

from abc import ABCMeta, abstractmethod


class IFilterService(metaclass=ABCMeta):
    @abstractmethod
    def setGenreSearchTag(self, tag: str) -> None:
        pass

    @abstractmethod
    def setDirectorSearchTag(self, tag: str) -> None:
        pass

    @abstractmethod
    def genre_tag(self, folder_name: str) -> str | None:
        pass

    @abstractmethod
    def resolve_genre(self, genre: str) -> str | None:
        pass

    @abstractmethod
    def suggest_genres(self, genre: str) -> tuple[str, ...]:
        pass

    @abstractmethod
    def clean_folder_name(self, name: str) -> str:
        pass
