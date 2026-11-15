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
    GenresEnum.ACTION: (
        "Acción",
        "Action Film",
        "Action Movie",
        "Cine de acción",
        "Película de acción",
    ),
    GenresEnum.ACTION_ADVENTURE: (
        "Action and Adventure",
        "Acción y aventura",
        "Acción & aventura",
        "Adventure and Action",
        "Adventure & Action",
        "Aventura y acción",
        "Acción y aventuras",
        "Action + Adventure",
        "Acción + aventura",
    ),
    GenresEnum.ADULT: (
        "Adulto",
        "Adultos",
        "Para adultos",
        "Adult Film",
        "Adult Movie",
        "Cine para adultos",
        "Película para adultos",
    ),
    GenresEnum.ADVENTURE: (
        "Aventuras",
        "Aventura",
        "Adventure Film",
        "Adventure Movie",
        "Cine de aventuras",
        "Película de aventuras",
    ),
    GenresEnum.ANIMATION: (
        "Animación",
        "Animated",
        "Animado",
        "Animada",
        "Animated Film",
        "Animated Movie",
        "Cartoon",
        "Cartoons",
        "Dibujos animados",
        "Cine de animación",
        "Película animada",
    ),
    GenresEnum.ANIME: (
        "Animación japonesa",
        "Japanese Animation",
        "Japanimation",
        "Japanese Anime",
        "Anime japonés",
        "Cine de anime",
    ),
    GenresEnum.ANIMAL: (
        "Animals",
        "Animales",
        "Animal Film",
        "Película de animales",
        "Cine de animales",
    ),
    GenresEnum.BIOGRAPHY: (
        "Biografía",
        "Biográfico",
        "Biográfica",
        "Biographical",
        "Biopic",
        "Biographical Film",
        "Biographical Movie",
        "Película biográfica",
        "Cine biográfico",
    ),
    GenresEnum.BOLLYWOOD: (
        "Cine de Bollywood",
        "Bollywood Film",
        "Bollywood Movie",
        "Película de Bollywood",
    ),
    GenresEnum.COMEDY: (
        "Comedia",
        "Comedy Film",
        "Comedy Movie",
        "Cine cómico",
        "Cine de comedia",
        "Película cómica",
    ),
    GenresEnum.CRIME: (
        "Crimen",
        "Crímenes",
        "Policial",
        "Policíaca",
        "Policíaco",
        "Crime Film",
        "Crime Movie",
        "Cine criminal",
        "Cine policíaco",
        "Película policial",
        "Película policíaca",
    ),
    GenresEnum.DISASTER: (
        "Disasters",
        "Desastre",
        "Desastres",
        "Catástrofe",
        "Catástrofes",
        "Disaster Film",
        "Disaster Movie",
        "Catastrophe Film",
        "Cine de catástrofes",
        "Película de desastres",
    ),
    GenresEnum.DOCUMENTARY: (
        "Documental",
        "Documentales",
        "Food",
        "Home and Garden",
        "Home & Garden",
        "Docu",
        "Documentary Film",
        "Documentary Movie",
        "Cine documental",
        "Película documental",
    ),
    GenresEnum.DRAMA: (
        "Drama Film",
        "Drama Movie",
        "Dramático",
        "Dramática",
        "Cine dramático",
        "Película dramática",
    ),
    GenresEnum.EASTERN: (
        "Oriental",
        "Cine oriental",
        "Eastern Film",
        "Eastern Movie",
        "Película oriental",
    ),
    GenresEnum.EROTIC: (
        "Erótica",
        "Erótico",
        "Erotismo",
        "Cine erótico",
        "Erotic Film",
        "Erotic Cinema",
        "Película erótica",
    ),
    GenresEnum.FAMILY: (
        "Familiar",
        "Familia",
        "Children",
        "Para toda la familia",
        "Family Film",
        "Family Movie",
        "Cine familiar",
        "Película familiar",
    ),
    GenresEnum.FAN_FILM: (
        "Fanfilm",
        "Película de fans",
        "Película hecha por fans",
        "Fan-made Film",
        "Fan Movie",
        "Cine de fans",
        "Película hecha por aficionados",
    ),
    GenresEnum.FANTASY: (
        "Fantasía",
        "Fantasy Film",
        "Fantasy Movie",
        "Fantástico",
        "Fantástica",
        "Cine de fantasía",
        "Película de fantasía",
    ),
    GenresEnum.FILM_NOIR: (
        "Filmnoir",
        "Cine negro",
        "Classic Noir",
        "Classic Film Noir",
        "Cine negro clásico",
    ),
    GenresEnum.FOREIGN: (
        "Extranjera",
        "Extranjero",
        "Cine extranjero",
        "Foreign Film",
        "Foreign Movie",
        "Foreign Cinema",
        "Película extranjera",
    ),
    GenresEnum.GAME_SHOW: (
        "Gameshow",
        "Quiz Show",
        "Concurso",
        "Concursos",
        "Concurso de televisión",
        "Quizshow",
        "TV Quiz",
        "TV Game Show",
        "Concurso televisivo",
        "Programa de concursos",
    ),
    GenresEnum.HISTORY: (
        "Historia",
        "Histórica",
        "Histórico",
        "Historical",
        "Historical Film",
        "Historical Movie",
        "Cine histórico",
        "Película histórica",
    ),
    GenresEnum.HOLIDAY: (
        "Festividad",
        "Festividades",
        "Festivo",
        "Festiva",
        "Holiday Film",
        "Holiday Movie",
        "Película festiva",
        "Christmas Movie",
        "Cine navideño",
        "Película navideña",
    ),
    GenresEnum.HORROR: (
        "Terror",
        "Horror Film",
        "Horror Movie",
        "Scary Movie",
        "Cine de terror",
        "Película de terror",
    ),
    GenresEnum.INDIE: (
        "Independent",
        "Cine independiente",
        "Independiente",
        "Special Interest",
        "Indie Film",
        "Indie Movie",
        "Independent Film",
        "Independent Cinema",
        "Película independiente",
    ),
    GenresEnum.KIDS: (
        "Kid",
        "Infantil",
        "Niños",
        "Para niños",
        "Kids Film",
        "Kids Movie",
        "Cine infantil",
        "Película infantil",
        "Para niñas y niños",
    ),
    GenresEnum.MINI_SERIES: (
        "Miniseries",
        "Miniserie",
        "Mini-Serie",
        "TV Miniseries",
        "Limited Series",
        "Miniserie televisiva",
        "Serie limitada",
    ),
    GenresEnum.MUSIC: (
        "Música",
        "Cine de música",
        "Concert Film",
        "Película de concierto",
    ),
    GenresEnum.MUSICAL: (
        "Musicales",
        "Cine musical",
        "Musical Film",
        "Musical Movie",
        "Film musical",
        "Película musical",
    ),
    GenresEnum.MYSTERY: (
        "Misterio",
        "Mystery Film",
        "Mystery Movie",
        "Misterios",
        "Cine de misterio",
        "Película de misterio",
    ),
    GenresEnum.NEO_NOIR: (
        "Neonoir",
        "Cine neo-noir",
        "Cine negro moderno",
        "Modern Noir",
        "Noir contemporáneo",
        "Cine negro contemporáneo",
    ),
    GenresEnum.NEWS: (
        "Noticia",
        "Noticias",
        "Noticiero",
        "Informativo",
        "Newscast",
        "News Bulletin",
        "News Program",
        "Noticiario",
        "Telediario",
        "Programa de noticias",
    ),
    GenresEnum.REALITY_TV: (
        "Reality",
        "Reality Show",
        "Telerrealidad",
        "Telerealidad",
        "Tele realidad",
        "Reality Television",
        "Reality TV Show",
        "Reality Program",
        "Programa de telerrealidad",
    ),
    GenresEnum.ROAD_MOVIE: (
        "Roadmovie",
        "Road Film",
        "Película de carretera",
        "Cine de carretera",
        "Road Trip Film",
        "Road Trip Movie",
        "Película de viaje por carretera",
    ),
    GenresEnum.ROMANCE: (
        "Romántica",
        "Romántico",
        "Romantic",
        "Romance Film",
        "Romantic Film",
        "Romantic Movie",
        "Love Story",
        "Historia de amor",
        "Cine romántico",
        "Película romántica",
    ),
    GenresEnum.SCIENCE_FICTION: (
        "Ciencia ficción",
        "Sci-Fi",
        "SciFi",
        "Cifi",
        "Science Fiction Film",
        "Sci-Fi Movie",
        "Cine de ciencia ficción",
        "Película de ciencia ficción",
    ),
    GenresEnum.SCIENCE_FICTION_FANTASY: (
        "Sci-Fi and Fantasy",
        "SciFi & Fantasy",
        "SciFi and Fantasy",
        "Science Fiction & Fantasy",
        "Science Fiction and Fantasy",
        "Ciencia ficción y fantasía",
        "Ciencia ficción & fantasía",
        "Fantasy & Science Fiction",
        "Fantasy and Sci-Fi",
        "Fantasía y ciencia ficción",
    ),
    GenresEnum.SERIES: (
        "Serie",
        "TV Series",
        "Serie de TV",
        "Serie de televisión",
        "Television Series",
        "TV Serial",
        "Serie televisiva",
        "Serial televisivo",
    ),
    GenresEnum.SHORT: (
        "Short Film",
        "Corto",
        "Cortometraje",
        "Cortometrajes",
        "Shorts",
        "Short Movie",
        "Corto cinematográfico",
    ),
    GenresEnum.SILENT_MOVIE: (
        "Silent Film",
        "Cine mudo",
        "Película muda",
        "Silent Cinema",
        "Silent Picture",
        "Cine silente",
        "Película silente",
    ),
    GenresEnum.SOAP: (
        "Soap Opera",
        "Telenovela",
        "Culebrón",
        "Soap Operas",
        "TV Soap",
        "Telenovelas",
        "Culebrones",
    ),
    GenresEnum.SPORT: (
        "Deporte",
        "Deportes",
        "Sports",
        "Deportivo",
        "Deportiva",
    ),
    GenresEnum.SPORTING_EVENT: (
        "Sports Event",
        "Evento deportivo",
        "Live Sports Event",
        "Competición deportiva",
        "Competencia deportiva",
    ),
    GenresEnum.SPORTS_FILM: (
        "Sport Film",
        "Sports Movie",
        "Película deportiva",
        "Cine deportivo",
        "Sports Cinema",
        "Sports Picture",
        "Film deportivo",
        "Películas deportivas",
    ),
    GenresEnum.TALK_SHOW: (
        "Talk",
        "Talkshow",
        "Entrevistas",
        "Programa de entrevistas",
        "Programa de conversación",
        "Programa de charla",
        "Charla",
        "Chat Show",
        "Chatshow",
        "Interview Show",
        "Programa de entrevistas de TV",
    ),
    GenresEnum.THRILLER: (
        "Suspenso",
        "Suspense",
        "Thriller Film",
        "Thriller Movie",
        "Suspense Film",
        "Cine de suspenso",
        "Cine de suspense",
        "Película de suspenso",
        "Película de suspense",
    ),
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
        "Telemovie",
        "TV Feature",
        "Made-for-TV Film",
        "Made-for-Television Movie",
        "Película televisiva",
        "Película hecha para televisión",
    ),
    GenresEnum.WAR: (
        "Bélica",
        "Bélico",
        "Guerra",
        "War Film",
        "Cine bélico",
        "War Movie",
        "Cine de guerra",
        "Película de guerra",
        "Película bélica",
    ),
    GenresEnum.WAR_POLITICS: (
        "War and Politics",
        "Guerra y política",
        "Guerra & política",
        "Bélica y política",
        "Bélica & política",
        "Politics & War",
        "Politics and War",
        "Política y guerra",
    ),
    GenresEnum.WESTERN: (
        "Oeste",
        "Del oeste",
        "Cine del oeste",
        "Wéstern",
        "Cine de vaqueros",
        "Western Film",
        "Western Movie",
        "Cowboy Movie",
        "Vaqueros",
        "Cine vaquero",
        "Película del oeste",
    ),
}


# Related labels and subgenres are suggestions for the review report only.
GENRE_REVIEW_HINTS = {
    ("Black Comedy", "Dark Comedy", "Comedia negra", "Humor negro"): (
        GenresEnum.COMEDY,
    ),
    ("Romcom", "Romantic Comedy", "Comedia romántica"): (
        GenresEnum.COMEDY,
        GenresEnum.ROMANCE,
    ),
    ("Dramedy", "Comedy Drama", "Comedia dramática", "Comedia + Drama"): (
        GenresEnum.COMEDY,
        GenresEnum.DRAMA,
    ),
    (
        "Historical Drama",
        "Period Drama",
        "Drama histórico",
        "Drama de época",
        "Cine de época",
    ): (GenresEnum.DRAMA, GenresEnum.HISTORY),
    ("Romantic Drama", "Drama romántico"): (GenresEnum.DRAMA, GenresEnum.ROMANCE),
    ("Biographical Drama", "Drama biográfico"): (
        GenresEnum.BIOGRAPHY,
        GenresEnum.DRAMA,
    ),
    ("Docudrama", "Documentary Drama"): (GenresEnum.DOCUMENTARY, GenresEnum.DRAMA),
    ("Docuseries", "Serie documental", "Docuserie"): (
        GenresEnum.DOCUMENTARY,
        GenresEnum.SERIES,
    ),
    ("True Crime", "Crímenes reales", "Crimen real"): (
        GenresEnum.CRIME,
        GenresEnum.DOCUMENTARY,
    ),
    ("Music Documentary", "Documental musical", "Documental de música"): (
        GenresEnum.DOCUMENTARY,
        GenresEnum.MUSIC,
    ),
    ("Sports Documentary", "Documental deportivo"): (
        GenresEnum.DOCUMENTARY,
        GenresEnum.SPORT,
    ),
    ("Detective Fiction", "Detectives", "Whodunit", "Cine de detectives"): (
        GenresEnum.CRIME,
        GenresEnum.MYSTERY,
    ),
    ("Crime Thriller", "Thriller policial", "Suspenso policial"): (
        GenresEnum.CRIME,
        GenresEnum.THRILLER,
    ),
    ("Psychological Horror", "Terror psicológico"): (
        GenresEnum.HORROR,
        GenresEnum.THRILLER,
    ),
    ("Psychological Thriller", "Suspenso psicológico", "Thriller psicológico"): (
        GenresEnum.THRILLER,
    ),
    ("Erotic Thriller", "Thriller erótico", "Suspenso erótico"): (
        GenresEnum.EROTIC,
        GenresEnum.THRILLER,
    ),
    ("Noir", "Cine noir"): (GenresEnum.FILM_NOIR, GenresEnum.NEO_NOIR),
    ("Martial Arts", "Artes marciales", "Kung Fu", "Wuxia"): (
        GenresEnum.ACTION,
        GenresEnum.EASTERN,
    ),
    ("Superhero", "Superhéroes", "Cine de superhéroes"): (
        GenresEnum.ACTION,
        GenresEnum.FANTASY,
        GenresEnum.SCIENCE_FICTION,
    ),
    (
        "Cyberpunk",
        "Space Opera",
        "Ópera espacial",
        "Time Travel",
        "Viajes en el tiempo",
    ): (GenresEnum.SCIENCE_FICTION,),
    ("Paranormal", "Sobrenatural", "Supernatural"): (
        GenresEnum.FANTASY,
        GenresEnum.HORROR,
    ),
    ("Spaghetti Western", "Wéstern italiano"): (GenresEnum.WESTERN,),
    ("War Drama", "Drama bélico"): (GenresEnum.DRAMA, GenresEnum.WAR),
    ("Political Drama", "Drama político"): (GenresEnum.DRAMA, GenresEnum.WAR_POLITICS),
    ("Bollywood Musical", "Musical de Bollywood"): (
        GenresEnum.BOLLYWOOD,
        GenresEnum.MUSICAL,
    ),
}
