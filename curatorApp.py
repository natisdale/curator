import logging  # used for logging
# Image processing
from urllib.request import urlopen  # used in retrieving image
import io  # used to handle byte stream for image
from PIL import Image, ImageTk  # used to handle images
# GUI
from tkinter import Tk, Menu, BOTH, HORIZONTAL, X, IntVar, StringVar, END
from tkinter.ttk import Button, Checkbutton, Entry, Label, Panedwindow, Progressbar, Spinbox, Treeview
# Curator API
from curator import Museum, Query

import threading
from concurrent.futures import ThreadPoolExecutor
import queue

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)


class CuratorApp:
    ''' GUI for Metropolitan Museum Open Access API '''
    def __init__(self, root):
        self.museum = Museum(
            "Metropolitan Museum",
            "https://collectionapi.metmuseum.org/public/collection/v1/search?",
            "https://collectionapi.metmuseum.org/public/collection/v1/objects/"
        )
        self.queryObject = Query(self.museum)
        
        self.executor = ThreadPoolExecutor()
        self.artObjectQueue = queue.Queue()
        
        # Menu
        menubar = Menu(root)
        fileMenu = Menu(menubar)
        fileMenu.add_command(label="Load Favorites")
        fileMenu.add_command(label="Save Favorites")
        fileMenu.add_separator()
        fileMenu.add_command(label="Quit", command=root.quit)
        menubar.add_cascade(label='Curator', menu=fileMenu)
        helpMenu = Menu(menubar)
        helpMenu.add_command(label="About")
        menubar.add_cascade(label='Help', menu=helpMenu)
        root.config(menu=menubar)

        # Variables for GUI control values
        self.department = StringVar()
        self.classificationValue = StringVar()
        self.geoLocationValue = StringVar()
        self.hasImageValue = IntVar()
        self.isTitleSearchValue = IntVar()
        self.isHighlightValue = IntVar()
        self.isOnViewValue = IntVar()
        self.dateBeginValue = StringVar()
        self.dateEndValue = StringVar()
        self.window = Panedwindow(root, orient=HORIZONTAL)
        # Containers for controls
        self.controlFrame = Panedwindow(root, width=180, height=400)
        self.resultsFrame = Panedwindow(root, width=600, height=400)
        self.imageFrame = Panedwindow(root, width=600, height=400)
        # Widgets for controlFrame
        self.institution = Label(self.controlFrame, text='Museum')
        self.museumSelector = Spinbox(
            self.controlFrame,
            values=["New York Met Museum"]
        )
        self.museumSelector.set("New York Met Museum")
        self.search = Button(
            self.controlFrame,
            text='Search',
            command=self.runSearch
        )
        self.keyWordsOrTitle = Label(
            self.controlFrame,
            text="Title or Keywords"
        )
        self.query = Entry(self.controlFrame)
        self.query.insert(0, "The Laundress")
        self.isTitleSearch = Checkbutton(
            self.controlFrame,
            variable=self.isTitleSearchValue,
            onvalue=1,
            offvalue=0,
            text='Search in Title'
        )
        self.isTitleSearchValue.set(1)
        self.dept = Label(self.controlFrame, text='Department')
        departmentsList = self.museum.getDepartmentList()
        self.departmentSelector = Spinbox(
            self.controlFrame,
            values=departmentsList,
            textvariable=self.department,
            wrap=False
        )
        self.departmentSelector.set("European Paintings")
        self.classification = Label(self.controlFrame, text='Classification')
        classificatinList = self.museum.getClassifications()
        self.classificationSelector = Spinbox(
            self.controlFrame,
            values=classificatinList,
            textvariable=self.classificationValue,
            wrap=False
        )
        self.classificationSelector.set("Paintings")
        self.geo = Label(root, text='Geographic Location')
        self.geoLocationSelector = Spinbox(
            self.controlFrame,
            values=lambda: self.museum.getGeoLocations(),
            textvariable=self.geoLocationValue,
            wrap=False
        )
        self.hasImage = Checkbutton(
            self.controlFrame,
            variable=self.hasImageValue,
            onvalue=1,
            offvalue=0,
            text='Has Image'
        )
        self.hasImageValue.set(1)
        self.hasImage.configure(state='disabled')
        self.isHighlight = Checkbutton(
            self.controlFrame,
            variable=self.isHighlightValue,
            onvalue=1,
            offvalue=0,
            text='Is Highlight'
        )
        self.isHighlightValue.set(0)
        self.isOnView = Checkbutton(
            self.controlFrame,
            variable=self.isOnViewValue,
            text='On View'
        )
        self.isOnViewValue.set(1)
        self.yearBegin = Label(self.controlFrame, text='Year Range Start')
        self.dateBegin = Spinbox(
            self.controlFrame,
            from_=-4000,
            to=2021,
            textvariable=self.dateBeginValue,
        )
        self.dateBegin.set(-2000)
        self.yearEnd = Label(self.controlFrame, text='Year Range Finish')
        self.dateEnd = Spinbox(
            self.controlFrame,
            from_=-4000,
            to=2021,
            textvariable=self.dateEndValue,
            wrap=False
        )
        self.dateEnd.set(2021)
        self.progressbar = Progressbar(
            self.controlFrame,
            orient='horizontal',
            length=200
        )
        self.progressbar.config(mode='indeterminate')
        # Widgets for resultsFrame
        self.resultsTree = Treeview(self.resultsFrame, height=200)
        # browse option to only allow selection of single item
        self.resultsTree.config(selectmode='browse')
        self.resultsTree.bind('<<TreeviewSelect>>', self.showByUrl)
        # Widgets for imageFrame
        self.artObjectImage = Label(
            self.imageFrame,
            text='<image placeholder>'
        )

        # Updates image to WildCat Logo before controls are displayed
        self.displayLogo()

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
        self.progressbar.pack(fill=X)
        self.resultsTree.pack(fill=BOTH, expand=True)
        self.artObjectImage.pack(fill=BOTH, expand=True)


    def buildQuery(self):
        '''
        Pass paramters from GUI to the Query object to build the query string
        '''
        # Example of rest call for object search:
        # https://collectionapi.metmuseum.org/public/collection/v1/search?title=true&classification=PaintingsdepartmentId=11&isOnView=true&hasImages=true&isHighlight=false$dateBegin=-2000&dateEnd=2021&q=%22The%20Laundress%22
        if self.isTitleSearchValue.get() == 1:
            self.queryObject.setParameter("title", "true")
        else:
            self.queryObject.setParameter("title", "false")
        self.queryObject.setParameter(
            "classification",
            self.classificationValue.get()
        )
        self.queryObject.setParameter(
            "departmentId",
            str(self.museum.getDepartmentId(self.departmentSelector.get()))
        )
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

    def displayLogo(self):
        '''
        displayLogo(): load logo into artObjectImage control
        '''
        self.openedUrl = urlopen('https://www.csuchico.edu/style-guide/visual/_images/Chico-state-athletics-icon.png')
        self.objectImage = io.BytesIO(self.openedUrl.read())
        self.pilImage = Image.open(self.objectImage)
        self.tkImage = ImageTk.PhotoImage(self.pilImage)
        self.artObjectImage.config(image=self.tkImage)
        
    def queueArtObjects(self):
        '''
        queueArtObjects(): loads images in queue objects result set into a queue
        '''
        logging.debug('queueArtObjects thread running')
        resultSet = self.queryObject.fetchArtObjects()
        for artObject in resultSet:
            logging.debug('queueArtObjects adding objects to queue')
            self.artObjectQueue.put(artObject)
        logging.debug('queueArtObjects finished queueing Art Objects')
    
    def dequeueArtObjects(self):
        '''
        dequeueArtObjects: loads queued objects into TreeView contoller
        '''
        logging.debug('dequeueArtObjects thread running')
        while True:
            artObject = self.artObjectQueue.get()
            logging.debug('dequeueArtObjects: ' + artObject.title)
            if artObject.title == 'done':
                logging.debug('dequeueArtjects done')
                break
            else:
                logging.debug('dequeueArtObjects: inserting ' + artObject.title)
                self.executor.submit(self.resultsTree.insert(
                    '',
                    END,
                    artObject.imageUrl,
                    text=artObject.title
                ))
        self.executor.submit(self.displayLogo)
        self.progressbar.stop()

    
    def runSearch(self):
        '''
        Runs the rest query based on the paramters selected in GUI
        '''
        self.progressbar.start()
        # reset adapated from:
        # https://stackoverflow.com/questions/22812134/how-to-clear-an-entire-treeview-with-tkinter
        for i in self.resultsTree.get_children():
            self.resultsTree.delete(i)
        self.buildQuery()
        self.executor.submit(self.queueArtObjects)
        self.executor.submit(self.dequeueArtObjects)
        

    def showByUrl(self, event):
        '''
        Retrieve and display the image of the item selected in the tree
        '''
        for i in self.resultsTree.selection():
            logging.debug(i)
            self.openedUrl = urlopen(i)
            self.objectImage = io.BytesIO(self.openedUrl.read())
            self.pilImage = Image.open(self.objectImage)
            self.tkImage = ImageTk.PhotoImage(self.pilImage)
            self.artObjectImage.destroy()
            self.artObjectImage = Label(
                self.imageFrame,
                text='',
                image=self.tkImage
            )
            self.artObjectImage.pack(fill=BOTH, expand=True)


    def show(self, artObject):
        '''
        Retrieve and display the image of the given ArtObject
        '''
        # adapted from
        # https://www.daniweb.com/programming/software-development/code/493005/display-an-image-from-the-web-tkinter
        logging.debug("Retrieving image from " + str(artObject.getImageUrl()))
        self.openedUrl = urlopen(artObject.getImageUrl())
        self.objectImage = io.BytesIO(self.openedUrl.read())
        self.pilImage = Image.open(self.objectImage)
        self.tkImage = ImageTk.PhotoImage(self.pilImage)
        self.artObjectImage.config(image=self.tkImage)


def main():
    root = Tk()
    root.title("Curator")
    root.geometry("1100x700+10+10")
    app = CuratorApp(root)
    root.mainloop()
    del app
    del root


if __name__ == "__main__":
    main()
