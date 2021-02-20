import curator

def test():
    user = curator.User("flast")
    assert "flast" == user.getName()

    museum = curator.Museum(
        name = "Metropolitan Museum", 
        searchUrlBase = "https://collectionapi.metmuseum.org/public/collection/v1/search?",
        objectUrlBase = "https://collectionapi.metmuseum.org/public/collection/v1/objects/"
    )
    assert museum.getSearchUrlBase() == "https://collectionapi.metmuseum.org/public/collection/v1/search?"
    assert museum.getObjectUrlBase() == "https://collectionapi.metmuseum.org/public/collection/v1/objects/"

    query = curator.Query(museum)
    query.setParameter("isOnView", "true")
    query.setParameter("title", "The Laundress")
    query.setParameter("q", "Daumier")
    response = query.runQuery()
    assert len(response) > 0
    user.favorites.append(response[0])
    assert user.favorites[0].getTitle() == "The Laundress"
