import requests
from urllib.parse import urlencode  #used to convert dictionary to rest parameters

class User:
    def __init__(self, name):
        self.name = name

class Museum:
    def __init__(self, name, searchUrlBase, objectUrlBase):
        self.name = name
        self.searchUrlBase = searchUrlBase
        self.objectUrlBase = objectUrlBase

    def getSearchUrlBase(self):
        return self.searchUrlBase

class Query:
    def __init__(self, museum):
        self.parameters = {}
        self.museum = museum
        self.setParameter("hasImage", "true")

    def setParameter(self, parameterName, parameterValue):
        self.parameters[parameterName] = parameterValue

    def unsetParameter(parameterName):
        del self.parameters[parameterName]

    def runQuery(self):
        matches = ObjectList()
        queryPayload = {}
        queryHeaders= {}
        q = self.museum.getSearchUrlBase()
        q = q + urlencode(self.parameters)
        response = requests.request("GET", q, headers=queryHeaders, data = queryPayload)
        jsonResponse = response.json()
        for id in jsonResponse['objectIDs']:
            objectHeaders = {}
            objectPayload = {}
            objectResponse = requests.request(
                "GET",
                self.museum.objectUrlBase+str(id),
                headers=objectHeaders,
                data=objectPayload
                )
            objectJsonResponse = objectResponse.json()
            print(objectJsonResponse['objectID'])
            print(objectJsonResponse['title'])
            print(objectJsonResponse['artistDisplayName'])
            print(objectJsonResponse['primaryImageSmall'])
            matches.addItem(ArtObject(
                objectJsonResponse['objectID'],
                objectJsonResponse['title'],
                objectJsonResponse['artistDisplayName'],
                objectJsonResponse['primaryImageSmall']
            ))
        return matches

class ObjectList:
    def __init__(self):
        self.items = []

    def addItem(self, artObject):
        self.items.append(artObject)

    def delItem(self, artObject):
        self.remote[ArtObject]

class ArtObject:
    def __init__(self, objectId, title, artist, imageUrl):
            self.objectId = objectId
            self.title = title
            self.artist = artist
            self.imageUrl = imageUrl

class Database:
    def __init__(self, dbPath):
        self.dbPath = dbPath

#class Exhibit(ObjectList):


def main():
    user = User("Patron2021")
    museum = Museum(
        name = "Metropolitan Museum", 
        searchUrlBase = "https://collectionapi.metmuseum.org/public/collection/v1/search?",
        objectUrlBase = "https://collectionapi.metmuseum.org/public/collection/v1/objects/"
    )
    query = Query(museum)
    query.setParameter("isOnView", "true")
    query.setParameter("title", "The Laundress")
    query.setParameter("q", "Daumier")
    response = query.runQuery()

if __name__ == "__main__":
    main()