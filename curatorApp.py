import logging # used for logging
# Image processing
from urllib.parse import urlencode  #used to convert dictionary to rest parameters
from urllib.request import urlopen # used in retrieving image
import io # used to handle byte stream for image
from PIL import Image, ImageTk  # used to handle images
# GUI
from tkinter import END, Frame, messagebox, Tk, TOP, BOTTOM, LEFT, RIGHT, BOTH, HORIZONTAL, SUNKEN, X, Y, BooleanVar, DoubleVar, IntVar, StringVar
from tkinter.ttk import Button, Checkbutton, Entry, Frame, Label, Panedwindow, Scale, Spinbox, Style, Treeview # this overrides older controls in tkinter with newer tkk versions
# Curator API
from curator import ArtObject, Database ,Museum, Query, User

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


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
        # Variables for GUI control values
        self.classificationValue = StringVar()
        self.geoLocationValue = StringVar()
        self.hasImageValue = IntVar()
        self.isTitleSearchValue = IntVar()
        self.isHighlightValue = IntVar()
        self.isOnViewValue = IntVar()
        self.dateBeginValue = StringVar()
        self.dateEndValue = StringVar()
        self.window = Panedwindow(root, orient = HORIZONTAL)
        # Containers for controls
        self.controlFrame = Panedwindow(root, width=180, height=400)
        self.resultsFrame = Panedwindow(root, width=600, height=400)
        self.imageFrame = Panedwindow(root, width=600, height=400)
        # Widgets for controlFrame
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
        # Widgets for resultsFrame
        self.resultsTree = Treeview(self.resultsFrame, height=200)
        self.resultsTree.config(selectmode='browse') # Only allow selection of single item
        self.resultsTree.bind('<<TreeviewSelect>>', self.showByUrl)
        # Widgets for imageFrame
        self.artObjectImage = Label(self.imageFrame, text='<image placeholder>')

        # Place controls
        self.window.pack(fill=BOTH, expand=True)
        self.window.add(self.controlFrame, weight=1)
        self.window.add(self.resultsFrame, weight=2)
        self.window.add(self.imageFrame, weight=4)
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
        # Example of rest call for object search:
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