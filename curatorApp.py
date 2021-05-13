import logging  # used for logging
import json     # used for encoding/decoding favorites
# Image processing
from urllib.request import urlopen  # used in retrieving image
import io  # used to handle byte stream for image
from PIL import Image, ImageTk  # used to handle images
# GUI
from tkinter import Tk, Menu, BOTH, HORIZONTAL, X, IntVar, StringVar, filedialog, messagebox
from tkinter.ttk import Button, Checkbutton, Entry, Label, Panedwindow, Progressbar, Spinbox, Treeview, Style
# Curator API
from curator import Museum, Query, User, ArtObject

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


class CuratorApp:
    ''' GUI for Metropolitan Museum Open Access API '''
    def __init__(self, root):
        self.museum = Museum(
            "Metropolitan Museum",
            "https://collectionapi.metmuseum.org/public/collection/v1/search?",
            "https://collectionapi.metmuseum.org/public/collection/v1/objects/"
        )
        self.queryObject = Query(self.museum)
        self.user = User('curator')
        
        # Menu
        menubar = Menu(root)
        fileMenu = Menu(menubar)
        fileMenu.add_command(label="Import Favorites", command=self.importFavorites)
        fileMenu.add_command(label="Export Favorites", command=self.exportFavorites)
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
        # resultTree config
        self.resultsTree.config(selectmode='browse', show='tree', columns=('ID', 'Artist', 'Date', 'Nationality', 'Medium', 'Favorite'), displaycolumns=['Favorite'])
        self.resultsTree.column('Favorite', anchor='center', width=30, stretch=False)
        self.resultsTree.bind('<ButtonRelease-1>', self._selectionHandler)
        # Widgets for imageFrame
        self.artObjectImage = Label(
            self.imageFrame,
            text='<image placeholder>'
        )
        self.artObjectDetails = Label(
            self.imageFrame,
            text=''
        )
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
        self.artObjectDetails.pack(fill=BOTH, expand=True)

        # Additional styling
        style = Style()
        style.configure("Treeview", rowheight=25)

        # Display favorites on startup (if set)
        self.user.loadFavorites()
        self.listFavorites()


    # Pass paramters from GUI to the Query object to build the query string
    def buildQuery(self):
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

    # Runs the rest query based on the paramters selected in GUI
    def runSearch(self):
        self.progressbar.start()
        # reset adapated from:
        # https://stackoverflow.com/questions/22812134/how-to-clear-an-entire-treeview-with-tkinter
        for i in self.resultsTree.get_children():
            self.resultsTree.delete(i)
        self.buildQuery()
        resultSet = self.queryObject.runQuery()
        # Iterate through results, and display the image of the first object
        searchResults = self.resultsTree.insert('', 'end', 'searchResults', text='Search Results')
        self.resultsTree.item("searchResults", open = True)
        for position, artObject in enumerate(resultSet):
            if position == 0:
                self.show(artObject)
            self.resultsTree.insert(
                searchResults,
                position,
                artObject.imageUrl,
                text=artObject.title,
                values=[
                    artObject.objectId,
                    artObject.artist, 
                    artObject.date, 
                    artObject.nationality, 
                    artObject.medium, 
                    self._getFavoriteIcon(self.user.isFavorite(artObject.objectId))
                ]
            )
            position += 1
        self.progressbar.stop()

        # Reload favorites list
        self.listFavorites()

    def showByUrl(self, i):
        logging.debug(i)
        self.openedUrl = urlopen(i.replace('_cur_fav_', ''))
        self.objectImage = io.BytesIO(self.openedUrl.read())
        self.pilImage = Image.open(self.objectImage)
        self.pilImage.thumbnail((self.imageFrame.winfo_width()-15, self.imageFrame.winfo_width()))
        self.tkImage = ImageTk.PhotoImage(self.pilImage)
        self.artObjectImage.destroy()
        self.artObjectImage = Label(
            self.imageFrame,
            text='',
            image=self.tkImage,
            anchor="center"
        )
        artist_value = ''.join(self.resultsTree.item(i, "value")[1])
        date_value = ''.join(self.resultsTree.item(i, "value")[2])
        nationality_val = ''.join(self.resultsTree.item(i, "value")[3])
        medium_val = ''.join(self.resultsTree.item(i, "value")[4])
        # logging.debug(self.resultsTree.item(i, "value")[2])
        self.artObjectDetails.destroy()
        self.artObjectDetails = Label(
        self.imageFrame,
        text='Artist: ' + artist_value +
            '\nDate: ' + date_value +
            '\nNationality: ' + nationality_val +
            '\nMedium: ' + medium_val
        )
        self.artObjectDetails.pack(fill=BOTH, expand=True)
        self.artObjectImage.pack(fill=BOTH, expand=True)

    # Retrieve and display the image of the given ArtObject
    def show(self, artObject):
        # adapted from
        # https://www.daniweb.com/programming/software-development/code/493005/display-an-image-from-the-web-tkinter
        logging.debug("Retrieving image from " + str(artObject.getImageUrl()))
        self.openedUrl = urlopen(artObject.getImageUrl())
        self.objectImage = io.BytesIO(self.openedUrl.read())
        self.pilImage = Image.open(self.objectImage)
        self.pilImage.thumbnail((self.imageFrame.winfo_width()-10, self.imageFrame.winfo_width()))
        self.tkImage = ImageTk.PhotoImage(self.pilImage)
        self.artObjectImage.config(image=self.tkImage)

    # Retrieve and display the image of the item selected in the tree
    def _selectionHandler(self, event):
        index = self.resultsTree.identify_row(event.y)
        column = self.resultsTree.identify_column(event.x)

        # Ignore clicks on the tree "parents"
        if index in ['favorites', 'searchResults']:
            return
        
        # "#1" (favorite) is the first visible column after the row's 
        # text value col (#0)
        if column == "#1":
            self._toggleFavorite(index)
        else:
            self.showByUrl(index)

    # Toggle item as favorite and update treeview
    def _toggleFavorite(self, i):
        logging.debug(f"Toggling favorite: {i}")
        resultsId = i.replace('_cur_fav_', '')
        favoritesId = f"_cur_fav_{resultsId}"

        artObject = ArtObject(
            objectId = self.resultsTree.item(i, "value")[0],
            title = self.resultsTree.item(i, "text"),
            artist = self.resultsTree.item(i, "value")[1],
            date = self.resultsTree.item(i, "value")[2],
            nationality = self.resultsTree.item(i, "value")[3],
            medium = self.resultsTree.item(i, "value")[4],
            imageUrl = i 
        )

        if self.user.isFavorite(artObject.objectId):
            self.user.removeFavorite(artObject)
            favIcon = False
        else:
            self.user.addFavorite(artObject)
            favIcon = True

        # Update both favorites and results item rows
        values = [
            artObject.objectId,
            artObject.artist,
            artObject.date,
            artObject.nationality,
            artObject.medium,
            self._getFavoriteIcon(favIcon)
        ]

        for id in [resultsId, favoritesId]:
            if self.resultsTree.exists(id):
                self.resultsTree.item(id, values = values)

        self.listFavorites()

    def listFavorites(self, expand = True):
        # Remove existing "favorites" tree item
        if (self.resultsTree.exists('favorites')): 
            self.resultsTree.delete('favorites') 

        favoritesSet = self.user.getFavorites()
        
        if len(favoritesSet) > 0:
            favListItem = self.resultsTree.insert('', 'end', 'favorites', text='Favorites')
            self.resultsTree.item("favorites", open = expand)

            for position, artObject in enumerate(favoritesSet):
                self.resultsTree.insert(
                    favListItem,
                    position,
                    '_cur_fav_' + artObject.imageUrl,
                    text=artObject.title,
                    values=[
                        artObject.objectId,
                        artObject.artist, 
                        artObject.date, 
                        artObject.nationality, 
                        artObject.medium, 
                        self._getFavoriteIcon(self.user.isFavorite(artObject.objectId))
                    ]
                )
                position += 1

    def _getFavoriteIcon(self, isFavorite):
        if isFavorite:
            return u"\u2605"
        else:
            return u"\u2606"

    def importFavorites(self):
        logging.debug('Importing favorites...')

        go = messagebox.askokcancel(
            "Overwrite Warning", 
            "Importing a favorites file will overwrite your current favorites. If you'd like to keep your favorites, use the \"Export Favorites\" option before continuing. Would you like to proceed?",
            default="cancel"
        )
        
        if go:
            try:
                file = filedialog.askopenfile(
                    mode="r", 
                    title='Import Favorites', 
                    filetypes=[('Curator Favorites', '*.curator')], 
                    defaultextension='.curator'
                )

                favorites = json.load(file)
                for f in favorites:
                    self.user.addFavorite(ArtObject(
                    f['objectId'],
                    f['title'], 
                    f['artist'], 
                    f['date'],
                    f['nationality'],
                    f['medium'],
                    f['imageUrl']
                    )
                )
                logging.debug(favorites)

                file.close()
            except TypeError as e:
                logging.debug(f'Couldn\'t convert JSON favorites to obj. {str(e)}')
            except Exception as e:
                logging.debug(f'Something went wrong importing favorites. {str(e)}')
            finally:
                if file:
                    file.close()

            self.listFavorites()

    def exportFavorites(self):
        logging.debug('Exporting favorites...')

        try:
            file = filedialog.asksaveasfile(
                mode='w', 
                title='Export Favorites', 
                filetypes=[('Curator Favorites', '*.curator')], 
                defaultextension='.curator'
            )
            favorites = self.user.getFavorites()
            json.dump(
                favorites, 
                file, 
                default=lambda o: o.__dict__, 
                sort_keys=True, 
                indent=4
            )
            file.close()
        except TypeError as e:
            logging.debug(f'Couldn\'t convert favorites to JSON. {str(e)}')
        except Exception as e:
            logging.debug(f'Something went wrong exporting favorites. {str(e)}')
        finally:
            if file:
                file.close()

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
