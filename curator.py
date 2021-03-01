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
from tkinter import END, Frame, messagebox, Tk, TOP, BOTTOM, LEFT, RIGHT, BooleanVar, DoubleVar, IntVar, StringVar
from tkinter.ttk import Button, Checkbutton, Entry, Frame, Label, Scale, Spinbox, Style # this overrides older controls in tkinter with newer tkk versions


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
        
        #controlFrame = Frame(root)
        #artFrame = Frame(root)
        
        # Create controls
        self.institution = Label(root, text='Museum')
        self.museumSelector = Spinbox(root, values=["New York Met Museum"])
        self.museumSelector.set("New York Met Museum")
        self.search = Button(root, text='Search', command=self.runSearch)
        self.keyWordsOrTitle = Label(root, text="Title or Keywoards")
        self.query = Entry(root)
        self.query.insert(0,"The Laundress")
        self.isTitleSearch = Checkbutton(root, variable=self.isTitleSearchValue, onvalue=1, offvalue=0, text='Search in Title')
        self.isTitleSearchValue.set(1)
        self.dept = Label(root, text='Department')
        self.departmentSelector = Spinbox(root, values=lambda: self.museum.getDepartmentList(), textvariable=self.department, wrap=False)
        self.departmentSelector.set("European Paintings")
        self.classification = Label(root, text = 'Classification')
        self.classificationSelector = Spinbox(root, values=lambda: self.museum.getClassifications(), textvariable=self.classificationValue, wrap=False)
        self.classificationSelector.set("Paintings")
        self.geo = Label(root, text = 'Geographic Location')
        self.geoLocationSelector = Spinbox(root, values=lambda: self.museum.getGeoLocations(), textvariable=self.geoLocationValue, wrap=False)
        self.hasImage = Checkbutton(root, variable=self.hasImageValue, onvalue = 1, offvalue = 0, text = 'Has Image')
        self.hasImageValue.set(1)
        self.hasImage.configure(state='disabled')
        self.isHighlight = Checkbutton(root, variable=self.isHighlightValue, onvalue = 1, offvalue = 0, text = 'Is Highlight')
        self.isHighlightValue.set(0)
        self.isOnView = Checkbutton(root, variable=self.isOnViewValue, text = 'On View')
        self.isOnViewValue.set(1)
        self.yearBegin = Label(root, text='Year Range Start')
        self.dateBegin = Spinbox(root,from_=-4000, to=2021,textvariable=self.dateBeginValue,)
        self.dateBegin.set(-2000)
        self.yearEnd = Label(root, text='Year Range Finish')
        self.dateEnd = Spinbox(root, from_=-4000, to=2021, textvariable=self.dateEndValue, wrap=False )
        self.dateEnd.set(2021)
        self.objectImage = Label(root, text='<image placeholder>')

        # Place controls
        self.institution.pack()
        self.museumSelector.pack()
        self.keyWordsOrTitle.pack()
        self.query.pack()
        self.isTitleSearch.pack()
        self.dept.pack()
        self.departmentSelector.pack()
        self.classification.pack()
        self.classificationSelector.pack()
        self.hasImage.pack()
        self.isHighlight.pack()
        self.isOnView.pack()
        self.yearBegin.pack()
        self.dateBegin.pack()
        self.yearEnd.pack()
        self.dateEnd.pack()
        self.search.pack()
        self.objectImage.pack()
        
        
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
        self.buildQuery()
        resultSet = self.queryObject.runQuery()
        self.objectImage.config(text=resultSet[0].imageUrl)

      
    def show(self, artObject):
        
        # adapted from https://www.daniweb.com/programming/software-development/code/493005/display-an-image-from-the-web-tkinter
        openedUrl = urlopen(artObject.getImageUrl())
        objectImage = io.BytesIO(openedUrl.read())
        pilImage = Image.open(objectImage)
        tkImage = ImageTk.PhotoImage(pilImage)
        label = Label(root, image=tkImage)
        label.grid(row=1, column=3)
        

def main():
    root = Tk()
    root.title="Curator"
    app = CuratorApp(root)
    root.mainloop()

""" 
    # Create an instance of a User
    user = User("guest")
    
    

    # Create an instance of a Query using with several parameters
    query = Query(museum)
    query.setParameter("isOnView", "true")
    query.setParameter("title", "The Laundress")
    query.setParameter("q", "Daumier")

    # Run the query (and additionaly query for details) and return an ObjectList
    response = query.runQuery()
    user.favorites.append(response[0])
    user.saveFavorites()

    # Instantiate a Display object and show a favorite    
    window = Window()
    window.show(user.favorites.pop())
 """
if __name__ == "__main__":
    main()