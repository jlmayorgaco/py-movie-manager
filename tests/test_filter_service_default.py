import unittest

import pytest

from config.GenresConfig import GenresEnum
from src.domain.classes.FilterServiceDefaultClass import FilterServiceDefault


class TestFilterServiceDefault(unittest.TestCase):
    def setUp(self):
        self.filter_service = FilterServiceDefault()
        self.filter_service.setGenres(["Action", "Comedy", "Drama", "Thriller"])
        self.filter_service.setGenreSearchTag("[g-*]")
        self.filter_service.setDirectorSearchTag("[d-*]")

    def test_legacy_resolver_does_not_guess_typos(self):
        self.assertEqual(
            self.filter_service.getGenreByMostLikelihood("Thriler"), "Unknown"
        )

    def test_clean(self):
        folder_name = "[g-Action][d-Spielberg] Movie Name"
        cleaned_name = self.filter_service.clean(folder_name)
        self.assertEqual(cleaned_name, "Movie Name")

    def test_getGenreByFolderName(self):
        folder_name = "[g-Drama] A Great Movie"
        genre = self.filter_service.getGenreByFolderName(folder_name)
        self.assertEqual(genre, "Drama")

    def test_getGenreByFolderName_unknown(self):
        folder_name = "A Movie Without Tags"
        genre = self.filter_service.getGenreByFolderName(folder_name)
        self.assertEqual(genre, "Unknown")

    def test_extractTags(self):
        folder_name = "[g-Comedy][d-Tarantino] A Funny Movie"
        tags = self.filter_service.extractTags(folder_name)
        self.assertEqual(tags, {"genre": "Comedy", "director": "Tarantino"})

    def test_extractTags_unknown(self):
        folder_name = "Untitled"
        tags = self.filter_service.extractTags(folder_name)
        self.assertEqual(tags, {"genre": "Unknown", "director": "Unknown"})


@pytest.mark.parametrize(
    ("genre", "expected"),
    [
        ("  BÉLICA  ", "WAR"),
        ("Be\u0301lica", "WAR"),
        ("Belico", "WAR"),
        ("Guerra", "WAR"),
        ("War", "WAR"),
        ("MuSiCa", "MUSIC"),
        ("Acción", "ACTION"),
        ("Aventura", "ADVENTURE"),
        ("Animación", "ANIMATION"),
        ("Biografía", "BIOGRAPHY"),
        ("Comedia", "COMEDY"),
        ("Crimen", "CRIME"),
        ("Documental", "DOCUMENTARY"),
        ("Drama", "DRAMA"),
        ("Familiar", "FAMILY"),
        ("Fantasía", "FANTASY"),
        ("Histórica", "HISTORY"),
        ("Terror", "HORROR"),
        ("Misterio", "MYSTERY"),
        ("Oeste", "WESTERN"),
        ("Romántica", "ROMANCE"),
        ("Ciencia Ficción", "SCIENCE_FICTION"),
        ("Ciencia   ficción", "SCIENCE_FICTION"),
        ("science_fiction", "SCIENCE_FICTION"),
        ("SCIENCE-FICTION", "SCIENCE_FICTION"),
        ("Sci-Fi", "SCIENCE_FICTION"),
        ("Suspense", "THRILLER"),
        ("Thriller", "THRILLER"),
        ("Película de Televisión", None),
        ("Comedia / Drama", None),
        ("Thriler", None),
        ("", None),
    ],
)
def test_resolve_genre_uses_explicit_normalized_mappings(genre, expected):
    service = FilterServiceDefault()
    service.setGenres([item.name for item in GenresEnum])
    assert service.resolve_genre(genre) == expected


def test_resolver_never_enables_an_unconfigured_genre():
    service = FilterServiceDefault()
    service.setGenres(["Music"])
    assert service.resolve_genre("Bélica") is None


@pytest.mark.parametrize("genre", list(GenresEnum))
def test_all_canonical_english_genre_labels(genre):
    service = FilterServiceDefault()
    service.setGenres([item.name for item in GenresEnum])
    assert service.resolve_genre(genre.value) == genre.name
    assert service.resolve_genre(genre.name) == genre.name


if __name__ == "__main__":
    unittest.main()
