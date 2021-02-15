# Author: Nathan Tisdale
# Purpose: proof of concept 'curator' app leveraging Met Museam api
  
import requests
from urllib.parse import urlencode  #used to convert dictionary to rest parameters
import sqlite3

class User:
    def __init__(self, name):
        self.name = name

    def getName(self):
        return self.name

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
            # print(objectJsonResponse['objectID'])
            # print(objectJsonResponse['title'])
            # print(objectJsonResponse['artistDisplayName'])
            # print(objectJsonResponse['primaryImageSmall'])
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
    
    def getObjectId(self):
        return self.objectId

    def getTitle(self):
        return self.title
    
    def getArtist(self):
        return self.artist
    
    def getImageUrl(self):
        return self.imageUrl

class Database:
    def __init__(self, dbPath):
        self.dbPath = dbPath
        self.dbConnect = sqlite3.connect(self.dbPath)
        self.dbCursor = self.dbConnect.cursor()
        self.dbCursor.execute('''CREATE TABLE zeronormal (user text, objectId text, title text, artist text, imageUrl text)''')

    def insertArtObject(self, user, artObject):
        self.dbCursor.execute('''INSERT INTO zeronormal (user, objectId, title, artist, imageUrl) VALUES (?, ?, ?, ?, ?);''', (user.getName(), str(artObject.getObjectId()), artObject.getTitle(), artObject.getArtist(), artObject.getImageUrl(),))

#class Exhibit(ObjectList):


def main():
    # Create db in memory for proof of concept
    db = Database(":memory:")
    # Create an instance of a User
    user = User("Patron2021")
    # Create an instance of Museum based on New York Metropolitan Museaum API
    museum = Museum(
        name = "Metropolitan Museum", 
        searchUrlBase = "https://collectionapi.metmuseum.org/public/collection/v1/search?",
        objectUrlBase = "https://collectionapi.metmuseum.org/public/collection/v1/objects/"
    )
    # Create an instance of a Query using with seveal parameters
    query = Query(museum)
    query.setParameter("isOnView", "true")
    query.setParameter("title", "The Laundress")
    query.setParameter("q", "Daumier")
    # Run the query and itterate thorugh the results 
    #   more specifically, runQuery will return results of subqueries
    #   based on ids returned with the above parameters
    response = query.runQuery()
    for item in response.items:
        # insert each itme into db as if favorited
        db.insertArtObject(user, item)
        print("Saved " + item.getTitle() + " to db in memory")
    


if __name__ == "__main__":
    main()