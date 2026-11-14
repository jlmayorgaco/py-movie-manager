from enum import Enum
class MovieGenre(Enum):
    ACTION = 'Action'
    ADVENTURE = 'Adventure'
    COMEDY = 'Comedy'
    DRAMA = 'Drama'
    HORROR = 'Horror'
    ROMANCE = 'Romance'
    THRILLER = 'Thriller'
    SCIENCE_FICTION = 'Science Fiction'
    FANTASY = 'Fantasy'
    ANIMATION = 'Animation'
    DOCUMENTARY = 'Documentary'
    CRIME = 'Crime'
    MYSTERY = 'Mystery'
    FAMILY = 'Family'
    HISTORY = 'History'
    WAR = 'War'
    MUSIC = 'Music'
    WESTERN = 'Western'
    BIOGRAPHY = 'Biography'
    SPORT = 'Sport'

class Genre:
    def __init__(self, make, model, year):
        self.make = make
        self.model = model
        self.year = year
        self.odometer_reading = 0

    def getGenreByFolder(self):
        match = re.search(r'\[g-(.*?)\]', folder_name)
        # Check if a match is found
        if match:
            genre = match.group(1)
            return genre
        else:
            return "Unknown"

