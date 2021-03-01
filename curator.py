# Author: Nathan Tisdale
# Purpose: proof of concept 'curator' app leveraging Met Museum Open Access API

import logging # used for logging
import requests # used for rest
from urllib.parse import urlencode  #used to convert dictionary to rest parameters
from urllib.request import urlopen # used in retrieving image
import sqlite3 # used for local cache of data
import io # used to handle byte stream for image
from PIL import Image, ImageTk  # used to handle images
#GUI
from tkinter import END, Frame, messagebox, Tk, TOP, BOTTOM, LEFT, RIGHT, BOTH, HORIZONTAL, SUNKEN, X, Y, BooleanVar, DoubleVar, IntVar, StringVar
from tkinter.ttk import Button, Checkbutton, Entry, Frame, Label, Panedwindow, Scale, Spinbox, Style, Treeview # this overrides older controls in tkinter with newer tkk versions


DB_PATH = "curator.db"
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

class User:
    def __init__(self, name):
        self.name = name
        self.favorites = []
        self.loadFavorites()
        logging.debug(("created user: " + self.name + " with " + str(len(self.favorites)) + " items"))

    def getName(self):
        return self.name

    def loadFavorites(self):
        db = Database(DB_PATH)
        self.favorites = db.getFavorites(self)
        if self.favorites == None:
            self.favorites = []
        del db

    def saveFavorites(self):
        for artObject in self.favorites:
            artObject.save(self)

class Museum:
    def __init__(self, name, searchUrlBase, objectUrlBase):
        self.name = name
        self.searchUrlBase = searchUrlBase
        self.objectUrlBase = objectUrlBase
        # TODO retrieve departments using rest and store in db
        self.departments = {
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
        self._classifications = [ "Ceramics", "Furniture", "Paintings", "Sculpture", "Textiles" ]

    def getSearchUrlBase(self):
        return self.searchUrlBase

    def getObjectUrlBase(self):
        return self.objectUrlBase

    def isValidParameter(self, key, value):
        #TODO: perform validation based on the Open Access API documentation
        return true

    def getDepartmentId(self, departmentName):
        # adapted from https://stackoverflow.com/questions/8023306/get-key-by-value-in-dictionary
        for name,id in self.departments.items():
            if name == departmentName:
                return id
        # return 0 if department not found
        return 0
    
    def getDepartmentList(self):
        return list(self.departments.keys())

    def getGeoLocations(self):
        return self._geoLocations

    def getClassifications(self):
        return self._classifications
        

class Query:
    def __init__(self, museum):
        self.parameters = {}
        self.museum = museum
        self.setParameter("hasImage", "true")
        self.resultSet = []

    def setParameter(self, parameterName, parameterValue):
        logging.debug("Setting Paramater " + parameterName + ":" + parameterValue)
        self.parameters[parameterName] = parameterValue

    def unsetParameter(parameterName):
        del self.parameters[parameterName]

    def runQuery(self):
        resultSet = []
        queryPayload = {}
        queryHeaders= {}
        q = self.museum.getSearchUrlBase()
        q = q + urlencode(self.parameters)
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
                self.museum.getObjectUrlBase()+str(id),
                headers=objectHeaders,
                data=objectPayload
                )
            objectJsonResponse = objectResponse.json()
            resultSet.append(ArtObject(
                objectJsonResponse['objectID'],
                objectJsonResponse['title'],
                objectJsonResponse['artistDisplayName'],
                objectJsonResponse['primaryImageSmall']
            ))
        return resultSet

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
        resultSet = []
        self.dbCursor.execute("SELECT objectId, title, artist, imageUrl from zeronormal where user=?;", (user.getName(),))
        rows = self.dbCursor.fetchall()
        for row in rows:
            resultSet.append(ArtObject(row[0], row[1], row[2], row[3]))
        return resultSet

    def __del__(self):
        self.dbConnect.close
        logging.debug("Releasing Database resource")    
    
class CuratorApp:
    def __init__(self, root):
        # Create an instance of Museum based on New York Metropolitan Museum API
        self.museum = Museum(
            name = "Metropolitan Museum", 
            searchUrlBase = "https://collectionapi.metmuseum.org/public/collection/v1/search?",
            objectUrlBase = "https://collectionapi.metmuseum.org/public/collection/v1/objects/"
        )
        self.queryObject = Query(self.museum)

        self.department = StringVar()
        self.classificationValue = StringVar()
        self.geoLocationValue = StringVar()
        self.hasImageValue = IntVar()
        self.isTitleSearchValue = IntVar()
        self.isHighlightValue = IntVar()
        self.isOnViewValue = IntVar()
        self.dateBeginValue = StringVar()
        self.dateEndValue = StringVar()
        
        self.window = Panedwindow(root, orient = HORIZONTAL)
        
        self.controlFrame = Panedwindow(root, width=180, height=400)
        self.resultsFrame = Panedwindow(root, width=600, height=400)
        self.imageFrame = Panedwindow(root, width=600, height=400)
        
        # Create controls
        self.institution = Label(self.controlFrame, text='Museum')
        self.museumSelector = Spinbox(self.controlFrame, values=["New York Met Museum"])
        self.museumSelector.set("New York Met Museum")
        self.search = Button(self.controlFrame, text='Search', command=self.runSearch)
        self.keyWordsOrTitle = Label(self.controlFrame, text="Title or Keywoards")
        self.query = Entry(self.controlFrame)
        self.query.insert(0,"The Laundress")
        self.isTitleSearch = Checkbutton(self.controlFrame, variable=self.isTitleSearchValue, onvalue=1, offvalue=0, text='Search in Title')
        self.isTitleSearchValue.set(1)
        self.dept = Label(self.controlFrame, text='Department')
        self.departmentSelector = Spinbox(self.controlFrame, values=lambda: self.museum.getDepartmentList(), textvariable=self.department, wrap=False)
        self.departmentSelector.set("European Paintings")
        self.classification = Label(self.controlFrame, text = 'Classification')
        self.classificationSelector = Spinbox(self.controlFrame, values=lambda: self.museum.getClassifications(), textvariable=self.classificationValue, wrap=False)
        self.classificationSelector.set("Paintings")
        self.geo = Label(root, text = 'Geographic Location')
        self.geoLocationSelector = Spinbox(self.controlFrame, values=lambda: self.museum.getGeoLocations(), textvariable=self.geoLocationValue, wrap=False)
        self.hasImage = Checkbutton(self.controlFrame, variable=self.hasImageValue, onvalue = 1, offvalue = 0, text = 'Has Image')
        self.hasImageValue.set(1)
        self.hasImage.configure(state='disabled')
        self.isHighlight = Checkbutton(self.controlFrame, variable=self.isHighlightValue, onvalue = 1, offvalue = 0, text = 'Is Highlight')
        self.isHighlightValue.set(0)
        self.isOnView = Checkbutton(self.controlFrame, variable=self.isOnViewValue, text = 'On View')
        self.isOnViewValue.set(1)
        self.yearBegin = Label(self.controlFrame, text='Year Range Start')
        self.dateBegin = Spinbox(self.controlFrame,from_=-4000, to=2021,textvariable=self.dateBeginValue,)
        self.dateBegin.set(-2000)
        self.yearEnd = Label(self.controlFrame, text='Year Range Finish')
        self.dateEnd = Spinbox(self.controlFrame, from_=-4000, to=2021, textvariable=self.dateEndValue, wrap=False )
        self.dateEnd.set(2021)
        
        # resultsFrame widgets
        self.resultsTree = Treeview(self.resultsFrame, height=200)
        self.resultsTree.config(selectmode='browse') # Only allow selection of single item
        self.resultsTree.bind('<<TreeviewSelect>>', self.showByUrl)
        
        # imageFrame widgets
        self.artObjectImage = Label(self.imageFrame, text='<image placeholder>')

        # Place controls
        self.window.pack(fill=BOTH, expand=True)
        self.window.add(self.controlFrame, weight=1)
        #self.controlFrame.pack(side=LEFT)
        self.window.add(self.resultsFrame, weight=2)
        #self.resultsFrame.pack(side=LEFT)
        self.window.add(self.imageFrame, weight=4)
        #self.imageFrame.pack(side=LEFT)
        self.institution.pack(fill=X)
        self.museumSelector.pack(fill=X)
        self.keyWordsOrTitle.pack(fill=X)
        self.query.pack(fill=X)
        self.isTitleSearch.pack(fill=X)
        self.dept.pack(fill=X)
        self.departmentSelector.pack(fill=X)
        self.classification.pack(fill=X)
        self.classificationSelector.pack(fill=X)
        self.hasImage.pack(fill=X)
        self.isHighlight.pack(fill=X)
        self.isOnView.pack(fill=X)
        self.yearBegin.pack(fill=X)
        self.dateBegin.pack(fill=X)
        self.yearEnd.pack(fill=X)
        self.dateEnd.pack(fill=X)
        self.search.pack(fill=X)
        self.resultsTree.pack(fill=BOTH, expand=True)
        self.artObjectImage.pack(fill=BOTH, expand=True)
        
        
    def buildQuery(self):
        # https://collectionapi.metmuseum.org/public/collection/v1/search?title=true&classification=PaintingsdepartmentId=11&isOnView=true&hasImages=true&isHighlight=false$dateBegin=-2000&dateEnd=2021&q=%22The%20Laundress%22
        if self.isTitleSearchValue.get() == 1:
            self.queryObject.setParameter("title", "true")
        else:
            self.queryObject.setParameter("title", "false")
        self.queryObject.setParameter("classification", self.classificationValue.get())
        self.queryObject.setParameter("departmentId", str(self.museum.getDepartmentId(self.departmentSelector.get())))
        if self.isOnViewValue.get() == 1:
            self.queryObject.setParameter("isOnView", "true")
        else:
            self.queryObject.setParameter("isOnView", "false")
        if self.hasImageValue.get() == 1:
            self.queryObject.setParameter("hasImages", "true")
        else:
            self.queryObject.setParameter("hasImages", "false")
        if self.isHighlightValue.get() == 1:
            self.queryObject.setParameter("isHighlight", "true")
        else:
            self.queryObject.setParameter("isHighlight", "false")
        self.queryObject.setParameter("dateBegin", self.dateBeginValue.get())
        self.queryObject.setParameter("dateEnd", self.dateEndValue.get())
        self.queryObject.setParameter("q", self.query.get())


    def runSearch(self):
        # reset adapated from:
        # https://stackoverflow.com/questions/22812134/how-to-clear-an-entire-treeview-with-tkinter
        for i in self.resultsTree.get_children():
            self.resultsTree.delete(i)
        self.buildQuery()
        resultSet = self.queryObject.runQuery()
        position = 0
        for artObject in resultSet:
            if position == 0:
                self.show(artObject)
            self.resultsTree.insert('', position, artObject.imageUrl, text=artObject.title )
            position += 1


    def showByUrl(self, event):
        for i in self.resultsTree.selection():
            logging.debug(i)
            #self.artObjectImage.config(text=i)
            self.openedUrl = urlopen(i)
            self.objectImage = io.BytesIO(self.openedUrl.read())
            self.pilImage = Image.open(self.objectImage)
            self.tkImage = ImageTk.PhotoImage(self.pilImage)
            self.artObjectImage.destroy()
            self.artObjectImage = Label(self.imageFrame, text='', image=self.tkImage)
            self.artObjectImage.pack(fill=BOTH, expand=True)


    def show(self, artObject):
        # adapted from https://www.daniweb.com/programming/software-development/code/493005/display-an-image-from-the-web-tkinter
        logging.debug("Retrieving image from " + str(artObject.getImageUrl()))
        self.openedUrl = urlopen(artObject.getImageUrl())
        self.objectImage = io.BytesIO(self.openedUrl.read())
        self.pilImage = Image.open(self.objectImage)
        self.tkImage = ImageTk.PhotoImage(self.pilImage)
        #label = Label(root, image=tkImage)
        self.artObjectImage.config(image=self.tkImage)
        #label.grid(row=1, column=3)

        

def main():
    root = Tk()
    root.title="Curator"
    root.geometry("1100x700+10+10")
    app = CuratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()