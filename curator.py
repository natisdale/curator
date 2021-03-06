# Author: Nathan Tisdale
# Purpose: proof of concept 'curator' app leveraging Met Museum Open Access API

import logging # used for logging
import requests # used for rest
from urllib.parse import urlencode  #used to convert dictionary to rest parameters
from urllib.request import urlopen # used in retrieving image
import sqlite3 # used for local cache of data
import io # used to handle byte stream for image
from PIL import Image, ImageTk  # used to handle images
import pandas # for parsing sql
#GUI
from tkinter import END, Frame, messagebox, Tk, TOP, BOTTOM, LEFT, RIGHT, BOTH, HORIZONTAL, SUNKEN, X, Y, BooleanVar, DoubleVar, IntVar, StringVar
from tkinter.ttk import Button, Checkbutton, Entry, Frame, Label, Panedwindow, Scale, Spinbox, Style, Treeview # this overrides older controls in tkinter with newer tkk versions
from concurrent.futures import ThreadPoolExecutor

DB_PATH = "curator.db"
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

class User:
    def __init__(self, name):
        self._name = name
        self._favorites = []
        self.loadFavorites()
        logging.debug(("created user: " + self._name + " with " + str(len(self._favorites)) + " items"))

    def getName(self):
        return self._name

    def loadFavorites(self):
        __db = Database(DB_PATH)
        self._favorites = __db.getFavorites(self)
        if self._favorites == None:
            self._favorites = []
        del __db

    def saveFavorites(self):
        for artObject in self._favorites:
            artObject.save(self)

    def getFavorites(self):
        self.loadFavorites()
        return self._favorites

    def addFavorite(self, artObject):
        if not self.isFavorite(artObject.objectId):
            logging.debug(f'Adding favorite with ID {artObject.objectId}')
            self._favorites.append(artObject)

            # Save favorites whenever a new one is added.
            self.saveFavorites()
        else:
            logging.debug(f'Art object {artObject.objectId} is already a favorite')

    def removeFavorite(self, artObject):
        artObject.remove(self)
        self.loadFavorites()

    def isFavorite(self, objectId):
        for f in self._favorites:
            # artObject IDs from query are int, those from db are str - convert 
            # to str before check
            if f.objectId == str(objectId):
                return True
        return False


class Museum:
    def __init__(self, name, searchUrlBase, objectUrlBase):
        self._name = name
        self._searchUrlBase = searchUrlBase
        self._objectUrlBase = objectUrlBase
        # TODO retrieve departments using rest and store in db
        self._departments = {
            "American Decorative Arts" : 1,
            "Ancient Near Eastern Art" : 3,
            "Arms and Armor" : 4,
            "Arts of Africa, Oceania, and the Americas" : 5,
            "Asian Art" : 6,
            "The Cloisters" : 7,
            "The Costume Institute" : 8,
            "Drawings and Prints" : 9,
            "Egyptian Art" : 10,
            "European Paintings" : 11,
            "European Sculpture and Decorative Arts" : 12,
            "Greek and Roman Art" : 13,
            "Islamic Art" : 14,
            "The Robert Lehman Collection" : 15,
            "The Libraries" : 16,
            "Medieval Art" : 17,
            "Musical Instruments" : 18,
            "Photographs" : 19,
            "Modern Art" : 21,
        }
        self._geoLocations = [ "Europe", "France", "Paris", "China", "New York" ]
        self._classifications = self.get_classifications()

    def getSearchUrlBase(self):
        return self._searchUrlBase

    def getObjectUrlBase(self):
        return self._objectUrlBase

    def isValidParameter(self, key, value):
        #TODO: perform validation based on the Open Access API documentation
        return True

    def getDepartmentId(self, departmentName):
        # adapted from https://stackoverflow.com/questions/8023306/get-key-by-value-in-dictionary
        for name,id in self._departments.items():
            if name == departmentName:
                return id
        # return 0 if department not found
        return 0
    
    def getDepartmentList(self):
        return list(self._departments.keys())

    def getGeoLocations(self):
        return self._geoLocations

    def getClassifications(self):
        return self._classifications

    def get_classifications(self):
        print("getting classifications")
        conn=sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='classifications' ''')
        if cursor.fetchone()[0]==1 :
            print('Table exists.')
            print("classifications")
        else:
            print("making classifications")
            exec(open("parse_to_sql.py").read())
        query = ('''SELECT Classification FROM classifications;''')
        try:
            cursor.execute(query)
            rows =cursor.fetchall()
            temp = []
            for i in rows:
                temp.append(i[0])
            conn.commit()
            return temp
        except NameError:
            print(NameError)
            return []
        

class Query:
    def __init__(self, museum):
        self._parameters = {}
        self._museum = museum
        self.setParameter("hasImage", "true")
        self.objectSet = []
        self.resultSet = []
        self.state = 'new'

    def setParameter(self, parameterName, parameterValue):
        logging.debug("Setting Paramater " + parameterName + ":" + parameterValue)
        self._parameters[parameterName] = parameterValue

    def unsetParameter(self, parameterName):
        del self._parameters[parameterName]

    def _fetchObjectIds(self):
        logging.debug('_fetchObjectIds started')
        self.objectSet = []
        queryPayload = {}
        queryHeaders= {}
        q = self._museum.getSearchUrlBase()
        q = q + urlencode(self._parameters)
        logging.debug(q)
        response = requests.request("GET", q, headers=queryHeaders, data = queryPayload)
        jsonResponse = response.json()
        logging.debug("Rest query received " + str(len(jsonResponse)) + " matches")
        logging.debug(str(jsonResponse))
        if jsonResponse['objectIDs']:
            for id in jsonResponse['objectIDs']:
                self.objectSet.append(id)
        return len(self.objectSet)


    def _fetchArtObject(self, id):
        logging.debug('_fetchArtObject started')
        objectHeaders = {}
        objectPayload = {}
        objectResponse = requests.request(
            "GET",
            self._museum.getObjectUrlBase()+str(id),
            headers=objectHeaders,
            data=objectPayload
            )
        objectJsonResponse = objectResponse.json()
        artObject = ArtObject(
            objectJsonResponse['objectID'],
            objectJsonResponse['title'],
            objectJsonResponse['artistDisplayName'],
            objectJsonResponse['objectDate'],
            objectJsonResponse['artistNationality'],
            objectJsonResponse['medium'],
            objectJsonResponse['primaryImageSmall']
        )
        return(artObject)

    def fetchArtObjects(self):
        logging.debug('fetArtObjects starting')
        self.resultSet = []
        self._fetchObjectIds()
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self._fetchArtObject, id) for id in self.objectSet]
        for f in futures:
            self.resultSet.append(f.result())
        finishedToken = ArtObject(
            'done',
            'done',
            'done',
            'done',
            'done',
            'done',
            'done'
        )
        self.resultSet.append(finishedToken)
        return self.resultSet
        

    def threadedQuery(self):
        self.resultSet = []
        self.fetchObjectIds()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self.fetchDetails)
            logging.debug('Number of Ids retrieved: ', future.result())


    # This is needed for CI testing
    def runQuery(self):
        resultSet = []
        queryPayload = {}
        queryHeaders= {}
        q = self._museum.getSearchUrlBase()
        q = q + urlencode(self._parameters)
        logging.debug(q)
        response = requests.request("GET", q, headers=queryHeaders, data = queryPayload)
        jsonResponse = response.json()
        logging.debug("Rest query reseived " + str(len(jsonResponse)) + " matches")
        logging.debug(str(jsonResponse))
        for id in jsonResponse['objectIDs']:
            objectHeaders = {}
            objectPayload = {}
            objectResponse = requests.request(
                "GET",
                self._museum.getObjectUrlBase()+str(id),
                headers=objectHeaders,
                data=objectPayload
                )
            objectJsonResponse = objectResponse.json()
            resultSet.append(ArtObject(
                objectJsonResponse['objectID'],
                objectJsonResponse['title'],
                objectJsonResponse['artistDisplayName'],
                objectJsonResponse['objectDate'],
                objectJsonResponse['artistNationality'],
                objectJsonResponse['medium'],
                objectJsonResponse['primaryImageSmall']
            ))
        return resultSet

class ArtObject:
    def __init__(self, objectId, title, artist, date, nationality, medium, imageUrl):
            self.objectId = objectId
            self.title = title
            self.artist = artist
            self.date = date
            self.nationality = nationality
            self.medium = medium
            self.imageUrl = imageUrl
    
    def getObjectId(self):
        return self.objectId

    def getTitle(self):
        return self.title

    def getArtist(self):
        return self.artist

    def getDate(self):
        return self.date

    def getNationality(self):
        return self.nationality

    def getMedium(self):
        return self.medium
    
    def getImageUrl(self):
        return self.imageUrl

    def save(self, user):
        db = Database(DB_PATH)
        db.insertArtObject(user, self)
        del db

    def remove(self, user):
        db = Database(DB_PATH)
        db.removeArtObject(user, self)
        del db

class Database:
    def __init__(self, dbPath):
        self.dbPath = dbPath
        self.dbConnect = sqlite3.connect(self.dbPath)
        self.dbCursor = self.dbConnect.cursor()
        self.dbCursor.execute('''CREATE TABLE IF NOT EXISTS zeronormal (user text, objectId text, title text, artist text, date text, nationality text, medium text, imageUrl text, PRIMARY KEY (user, objectId))''')
        self.dbConnect.commit()
        logging.debug("Database object created successfully")

    def insertArtObject(self, user, artObject):
        logging.debug("Peristing favorites")
        self.dbCursor.execute('''INSERT OR REPLACE INTO zeronormal (user, objectId, title, artist, date, nationality, medium, imageUrl) VALUES (?, ?, ?, ?, ?, ?, ?, ?);''', (user.getName(), str(artObject.getObjectId()), artObject.getTitle(), artObject.getArtist(), artObject.getDate(), artObject.getNationality(), artObject.getMedium(), artObject.getImageUrl(),))
        self.dbConnect.commit()

    def removeArtObject(self, user, artObject):
        logging.debug("Removing from favorites table")
        self.dbCursor.execute('''DELETE FROM zeronormal WHERE user=? AND objectId=?;''', (user.getName(), str(artObject.getObjectId())))
        self.dbConnect.commit()

    def getFavorites(self, user):
        logging.debug("Checking for persisted favorites")
        resultSet = []
        self.dbCursor.execute("SELECT objectId, title, artist, date, nationality, medium, imageUrl from zeronormal where user=? ORDER BY title ASC;", (user.getName(),))
        rows = self.dbCursor.fetchall()
        for row in rows:
            resultSet.append(ArtObject(row[0], row[1], row[2], row[3], row[4], row[5], row[6]))
        return resultSet

    def __del__(self):
        self.dbConnect.close
        logging.debug("Releasing Database resource")
