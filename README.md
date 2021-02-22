# Curator

This project combines my interest in art and technology.  As an art student I developed a great appreciation for visiting museums for an intimate look at works of art.  As a computer information systems student I wanted to explore how the New York Met Museums's Open Access API might be used on curating a sort of remote exhibition.

![Block Diagram](https://lucid.app/publicSegments/view/a0a86283-2144-4c98-81b4-93c183523ed8/image.jpeg "Block Diagram")

The Met Museum Curator application will allow a user to search the New York Metropolitan Museum collection for art and display images of objects in the collection.  The query is performed over rest using an api provided by the museum.  The initial query returns a list of object ids, and a second query must be performed for each object to retrieve the details about the object, including locations of images.  The object id, title, artist, and url for the main image can be saved to a local database.  An image is displayed by using the saved url to perform a third query to retrieve the image. 

The three main use case actors would be art enthusiasts, students, and professionals.
- The use case for enthusiasts primarily invovles building and displaying a collection of favorites
- Students would benefit form additional details and lists for their studies, whether for the studio or historical research
- Art professors, and art historians are expected to build lists for sharing with classes or readers

The domain for this project consists of the application and the Open Access API which provides access to the collection data.

![Domain Diagram](https://lucid.app/publicSegments/view/467828ed-7adb-448a-9f8d-f3f09488d20a/image.jpeg "Domain Diagram")

The essential objects are:
- User, similar in nature to how Netflix profiles work
- Museum, which provides context for the API
- Query, which provides constructin and running of searches
- Art Objects created based on the returned meta-data
- Database for preserving lists
- Window to display images
- and of course, the Open Access API
