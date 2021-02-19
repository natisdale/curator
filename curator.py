# Author: Nathan Tisdale
# Purpose: proof of concept 'curator' app leveraging Met Museum api

import logging # used for logging
import requests # used for rest
from urllib.parse import urlencode  #used to convert dictionary to rest parameters
from urllib.request import urlopen # used in retrieving image
import sqlite3 # used for local cache of data
import io # used to handle byte stream for image
from PIL import Image, ImageTk  # used to handle images
import tkinter as tk # used for gui

DB_PATH = "curator.db"
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

class User:
    def __init__(self, name):
        self.name = name
        self.favorites = ObjectList()
        self.loadFavorites()
        logging.debug(("created user: " + self.name + " with " + str(len(self.favorites.items)) + " items"))

    def getName(self):
        return self.name

    def loadFavorites(self):
        db = Database(DB_PATH)
        self.favorites = db.getFavorites(self)
        if self.favorites == None:
            self.favorites = ObjectList()
        del db

    def saveFavorites(self):
        for artObject in self.favorites.items:
            artObject.save(self)

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

    def saveItem(self, artObject):
        artObject.save()

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

    def save(self, user):
        db = Database(DB_PATH)
        db.insertArtObject(user, self)
        del db

class Database:
    def __init__(self, dbPath):
        self.dbPath = dbPath
        self.dbConnect = sqlite3.connect(self.dbPath)
        self.dbCursor = self.dbConnect.cursor()
        self.dbCursor.execute('''CREATE TABLE IF NOT EXISTS zeronormal (user text, objectId text, title text, artist text, imageUrl text, PRIMARY KEY (user, objectId))''')
        self.dbConnect.commit()
        logging.debug("Database object created successfully")

    def insertArtObject(self, user, artObject):
        logging.debug("Peristing favorites")
        self.dbCursor.execute('''INSERT OR REPLACE INTO zeronormal (user, objectId, title, artist, imageUrl) VALUES (?, ?, ?, ?, ?);''', (user.getName(), str(artObject.getObjectId()), artObject.getTitle(), artObject.getArtist(), artObject.getImageUrl(),))
        self.dbConnect.commit()

    def getFavorites(self, user):
        logging.debug("Checking for persisted favorites")
        resultSet = ObjectList()
        self.dbCursor.execute("SELECT objectId, title, artist, imageUrl from zeronormal where user=?;", (user.getName(),))
        rows = self.dbCursor.fetchall()
        for row in rows:
            resultSet.addItem(ArtObject(row[0], row[1], row[2], row[3]))
        return resultSet

    def __del__(self):
        self.dbConnect.close
        logging.debug("Releasing Database resource")    
    
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
    # Create an instance of a User
    user = User("guest")
    
    # Create an instance of Museum based on New York Metropolitan Museum API
    museum = Museum(
        name = "Metropolitan Museum", 
        searchUrlBase = "https://collectionapi.metmuseum.org/public/collection/v1/search?",
        objectUrlBase = "https://collectionapi.metmuseum.org/public/collection/v1/objects/"
    )

    # Create an instance of a Query using with several parameters
    query = Query(museum)
    query.setParameter("isOnView", "true")
    query.setParameter("title", "The Laundress")
    query.setParameter("q", "Daumier")

    # Run the query (and additinaly query for details) and return an ObjectList
    response = query.runQuery()
    user.favorites.addItem(response.items[0])
    user.saveFavorites()

    # Instatiate a Display object and show a favorite    
    window = Display()
    window.show(user.favorites.items.pop().getImageUrl())

if __name__ == "__main__":
    main()