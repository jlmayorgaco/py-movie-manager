"""Local destinations for tinyMediaManager, IMDb and TMDB genre labels."""

from enum import Enum


class GenresEnum(Enum):
    ACTION = "Action"
    ACTION_ADVENTURE = "Action & Adventure"
    ADULT = "Adult"
    ADVENTURE = "Adventure"
    ANIMATION = "Animation"
    ANIME = "Anime"
    ANIMAL = "Animal"
    BIOGRAPHY = "Biography"
    BOLLYWOOD = "Bollywood"
    COMEDY = "Comedy"
    CRIME = "Crime"
    DISASTER = "Disaster"
    DOCUMENTARY = "Documentary"
    DRAMA = "Drama"
    EASTERN = "Eastern"
    EROTIC = "Erotic"
    FAMILY = "Family"
    FAN_FILM = "Fan Film"
    FANTASY = "Fantasy"
    FILM_NOIR = "Film Noir"
    FOREIGN = "Foreign"
    GAME_SHOW = "Game Show"
    HISTORY = "History"
    HOLIDAY = "Holiday"
    HORROR = "Horror"
    INDIE = "Indie"
    KIDS = "Kids"
    MINI_SERIES = "Mini-Series"
    MUSIC = "Music"
    MUSICAL = "Musical"
    MYSTERY = "Mystery"
    NEO_NOIR = "Neo Noir"
    NEWS = "News"
    REALITY_TV = "Reality TV"
    ROAD_MOVIE = "Road Movie"
    ROMANCE = "Romance"
    SCIENCE_FICTION = "Science Fiction"
    SCIENCE_FICTION_FANTASY = "Sci-Fi & Fantasy"
    SERIES = "Series"
    SHORT = "Short"
    SILENT_MOVIE = "Silent Movie"
    SOAP = "Soap"
    SPORT = "Sport"
    SPORTING_EVENT = "Sporting Event"
    SPORTS_FILM = "Sports Film"
    TALK_SHOW = "Talk Show"
    THRILLER = "Thriller"
    TV_MOVIE = "TV Movie"
    WAR = "War"
    WAR_POLITICS = "War & Politics"
    WESTERN = "Western"


# English names and folder names are accepted directly. These are additional aliases.
GENRE_ALIASES = {
    GenresEnum.ACTION: ("Acción",),
    GenresEnum.ACTION_ADVENTURE: (
        "Action and Adventure",
        "Acción y aventura",
        "Acción & aventura",
    ),
    GenresEnum.ADULT: ("Adulto", "Adultos", "Para adultos"),
    GenresEnum.ADVENTURE: ("Aventuras", "Aventura"),
    GenresEnum.ANIMATION: ("Animación", "Animated", "Animado", "Animada"),
    GenresEnum.ANIME: ("Animación japonesa", "Japanese Animation"),
    GenresEnum.ANIMAL: ("Animals", "Animales"),
    GenresEnum.BIOGRAPHY: (
        "Biografía",
        "Biográfico",
        "Biográfica",
        "Biographical",
        "Biopic",
    ),
    GenresEnum.BOLLYWOOD: ("Cine de Bollywood",),
    GenresEnum.COMEDY: ("Comedia",),
    GenresEnum.CRIME: ("Crimen", "Crímenes", "Policial", "Policíaca", "Policíaco"),
    GenresEnum.DISASTER: (
        "Disasters",
        "Desastre",
        "Desastres",
        "Catástrofe",
        "Catástrofes",
    ),
    GenresEnum.DOCUMENTARY: (
        "Documental",
        "Documentales",
        "Food",
        "Home and Garden",
        "Home & Garden",
    ),
    GenresEnum.EASTERN: ("Oriental", "Cine oriental"),
    GenresEnum.EROTIC: ("Erótica", "Erótico", "Erotismo", "Cine erótico"),
    GenresEnum.FAMILY: ("Familiar", "Familia", "Children", "Para toda la familia"),
    GenresEnum.FAN_FILM: ("Fanfilm", "Película de fans", "Película hecha por fans"),
    GenresEnum.FANTASY: ("Fantasía",),
    GenresEnum.FILM_NOIR: ("Filmnoir", "Cine negro"),
    GenresEnum.FOREIGN: ("Extranjera", "Extranjero", "Cine extranjero", "Foreign Film"),
    GenresEnum.GAME_SHOW: (
        "Gameshow",
        "Quiz Show",
        "Concurso",
        "Concursos",
        "Concurso de televisión",
    ),
    GenresEnum.HISTORY: ("Historia", "Histórica", "Histórico", "Historical"),
    GenresEnum.HOLIDAY: ("Festividad", "Festividades", "Festivo", "Festiva"),
    GenresEnum.HORROR: ("Terror",),
    GenresEnum.INDIE: (
        "Independent",
        "Cine independiente",
        "Independiente",
        "Special Interest",
    ),
    GenresEnum.KIDS: ("Kid", "Infantil", "Niños", "Para niños"),
    GenresEnum.MINI_SERIES: ("Miniseries", "Miniserie", "Mini-Serie"),
    GenresEnum.MUSIC: ("Música",),
    GenresEnum.MUSICAL: ("Musicales", "Cine musical"),
    GenresEnum.MYSTERY: ("Misterio",),
    GenresEnum.NEO_NOIR: ("Neonoir", "Cine neo-noir", "Cine negro moderno"),
    GenresEnum.NEWS: ("Noticia", "Noticias", "Noticiero", "Informativo"),
    GenresEnum.REALITY_TV: (
        "Reality",
        "Reality Show",
        "Telerrealidad",
        "Telerealidad",
        "Tele realidad",
    ),
    GenresEnum.ROAD_MOVIE: (
        "Roadmovie",
        "Road Film",
        "Película de carretera",
        "Cine de carretera",
    ),
    GenresEnum.ROMANCE: ("Romántica", "Romántico", "Romantic"),
    GenresEnum.SCIENCE_FICTION: ("Ciencia ficción", "Sci-Fi", "SciFi", "Cifi"),
    GenresEnum.SCIENCE_FICTION_FANTASY: (
        "Sci-Fi and Fantasy",
        "SciFi & Fantasy",
        "SciFi and Fantasy",
        "Science Fiction & Fantasy",
        "Science Fiction and Fantasy",
        "Ciencia ficción y fantasía",
        "Ciencia ficción & fantasía",
    ),
    GenresEnum.SERIES: ("Serie", "TV Series", "Serie de TV", "Serie de televisión"),
    GenresEnum.SHORT: ("Short Film", "Corto", "Cortometraje", "Cortometrajes"),
    GenresEnum.SILENT_MOVIE: ("Silent Film", "Cine mudo", "Película muda"),
    GenresEnum.SOAP: ("Soap Opera", "Telenovela", "Culebrón"),
    GenresEnum.SPORT: ("Deporte", "Deportes", "Sports"),
    GenresEnum.SPORTING_EVENT: ("Sports Event", "Evento deportivo"),
    GenresEnum.SPORTS_FILM: (
        "Sport Film",
        "Sports Movie",
        "Película deportiva",
        "Cine deportivo",
    ),
    GenresEnum.TALK_SHOW: (
        "Talk",
        "Talkshow",
        "Entrevistas",
        "Programa de entrevistas",
        "Programa de conversación",
        "Programa de charla",
        "Charla",
    ),
    GenresEnum.THRILLER: ("Suspenso", "Suspense"),
    GenresEnum.TV_MOVIE: (
        "TV Film",
        "T.V. Movie",
        "Television Movie",
        "Television Film",
        "Made-for-TV Movie",
        "Película de televisión",
        "Película para televisión",
        "Película de TV",
        "Película para TV",
        "Telepelícula",
        "Telefilme",
        "Telefilm",
    ),
    GenresEnum.WAR: ("Bélica", "Bélico", "Guerra", "War Film", "Cine bélico"),
    GenresEnum.WAR_POLITICS: (
        "War and Politics",
        "Guerra y política",
        "Guerra & política",
        "Bélica y política",
        "Bélica & política",
    ),
    GenresEnum.WESTERN: (
        "Oeste",
        "Del oeste",
        "Cine del oeste",
        "Wéstern",
        "Cine de vaqueros",
    ),
}
