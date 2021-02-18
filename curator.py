# Author: Nathan Tisdale
# Purpose: proof of concept 'curator' app leveraging Met Museam api

import requests # used for rest
from urllib.parse import urlencode  #used to convert dictionary to rest parameters
from urllib.request import urlopen # used in retrieving image
import sqlite3 # used for local cache of data
import io  
from PIL import Image, ImageTk  # used to handle images
import tkinter as tk # used for gui


class User:
    def __init__(self, name):
        self.name = name
        self.favorites = ObjectList()

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
        self.resultSet = ObjectList()

    def setParameter(self, parameterName, parameterValue):
        self.parameters[parameterName] = parameterValue

    def unsetParameter(parameterName):
        del self.parameters[parameterName]

    def runQuery(self):
        resultSet = ObjectList()
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
            resultSet.addItem(ArtObject(
                objectJsonResponse['objectID'],
                objectJsonResponse['title'],
                objectJsonResponse['artistDisplayName'],
                objectJsonResponse['primaryImageSmall']
            ))
        return resultSet

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

    def getArtObjectUrls(self, user):
        self.dbCursor.execute("SELECT imageUrl from zeronormal where user=? limit 1", (user.getName(),))
        return self.dbCursor.fetchone()
    
class Display():
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Met Museum Curator")

    def show(self, imageUrl):
        # adapted from https://www.daniweb.com/programming/software-development/code/493005/display-an-image-from-the-web-tkinter
        openedUrl = urlopen(imageUrl)
        objectImage = io.BytesIO(openedUrl.read())
        pilImage = Image.open(objectImage)
        tkImage = ImageTk.PhotoImage(pilImage)
        label = tk.Label(self.root, image=tkImage)
        label.pack(padx=5, pady=5)
        self.root.mainloop()


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
        #print("Saved " + item.getTitle() + " to db in memory")
    
    cachedUrl = db.getArtObjectUrls(user)
    
    window = Display()
    window.show(cachedUrl[0])

    
    


if __name__ == "__main__":
    main()