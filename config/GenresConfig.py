# src/domain/classes/genres.py

from enum import Enum


class GenresEnum(Enum):
    ACTION = "Action"
    ADVENTURE = "Adventure"
    ANIMATION = "Animation"
    BIOGRAPHY = "Biography"
    COMEDY = "Comedy"
    CRIME = "Crime"
    DOCUMENTARY = "Documentary"
    DRAMA = "Drama"
    FAMILY = "Family"
    FANTASY = "Fantasy"
    HISTORY = "History"
    HORROR = "Horror"
    MUSIC = "Music"
    MYSTERY = "Mystery"
    ROMANCE = "Romance"
    SCIENCE_FICTION = "Science Fiction"
    SPORT = "Sport"
    THRILLER = "Thriller"
    WAR = "War"
    WESTERN = "Western"


# Explicit equivalents for the existing destination genres.
GENRE_ALIASES = {
    GenresEnum.ACTION: ("Acción",),
    GenresEnum.ADVENTURE: ("Aventuras", "Aventura"),
    GenresEnum.ANIMATION: ("Animación",),
    GenresEnum.BIOGRAPHY: ("Biografía", "Biográfico", "Biográfica"),
    GenresEnum.COMEDY: ("Comedia",),
    GenresEnum.CRIME: ("Crimen", "Policial"),
    GenresEnum.DOCUMENTARY: ("Documental",),
    GenresEnum.FAMILY: ("Familiar", "Familia"),
    GenresEnum.FANTASY: ("Fantasía",),
    GenresEnum.HISTORY: ("Historia", "Histórica", "Histórico"),
    GenresEnum.HORROR: ("Terror",),
    GenresEnum.MUSIC: ("Música", "Musical"),
    GenresEnum.MYSTERY: ("Misterio",),
    GenresEnum.ROMANCE: ("Romántica", "Romántico"),
    GenresEnum.SCIENCE_FICTION: ("Ciencia ficción", "Sci-Fi", "SciFi"),
    GenresEnum.SPORT: ("Deporte", "Deportes", "Sports"),
    GenresEnum.THRILLER: ("Suspenso", "Suspense"),
    GenresEnum.WAR: ("Bélica", "Bélico", "Guerra"),
    GenresEnum.WESTERN: ("Oeste",),
}
