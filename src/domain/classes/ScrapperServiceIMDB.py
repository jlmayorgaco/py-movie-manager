from ..interfaces.IScrapperInterface import IScrapper

class ScrapperServiceIMDB(IScrapper):

    def __init__(self):
        self.apiKey = None

    def __str__(self):
        return f''' 
            ScrapperServiceIMDB::apiKey <{self.apiKey}>
        '''

    def getMovieByNameAndYear(self, name, year):
        return 0

    def setApiKey(self, apikey):
        self.apiKey = apikey
        return 1
