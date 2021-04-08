# Curator, an app for accessing the Met Museum collection

This project explores how the New York Met Museum's [Open Access API](https://www.metmuseum.org/blogs/now-at-the-met/2018/met-collection-api) might be used in curating a sort of remote exhibition.

![Block Diagram](https://lucid.app/publicSegments/view/a0a86283-2144-4c98-81b4-93c183523ed8/image.jpeg "Block Diagram")

The Met Museum Curator application will allow a user to search the New York Metropolitan Museum collection for art and display images of objects in the collection.  The query is performed over rest using an api provided by the museum.  The initial query returns a list of object ids, and a second query must be performed for each object to retrieve the details about the object, including locations of images.  The object id, title, artist, and url for the main image can be saved to a local database.  An image is displayed by using the saved url to perform a third query to retrieve the image. 

The three main use case actors would be art enthusiasts, students, and professionals.
- The use case for enthusiasts primarily involves building and displaying a collection of favorites
- Students would benefit form additional details and lists for their studies, whether for the studio or historical research
- Art professors, and art historians are expected to build lists for sharing with classes or readers

![Class Diagram](https://lucid.app/publicSegments/view/9aa52c83-e456-4047-a86d-9a34cc37eedf/image.jpeg? "Class Diagram")

The essential objects are:
- User, similar in nature to how Netflix profiles work
- Query, which provides construction and running of searches
- Museum, which provides context for the API, including parameter validation
- Art Objects created based on the returned meta-data
- Database for preserving lists (including title and url to image)
- Window to display images
- and of course, the Open Access API

The graphical interface written in Python using Tkinter is shown below.  The left panel contains controls for setting query parameters.  The middle pane shows the titles of objects returned by a search.  Selecting an item from the results list displays the main image for that art object in the pane on the right.

![GUI Prototype](https://tisdale.info/images/curator-gui-dev.png? "GUI Prototype")
