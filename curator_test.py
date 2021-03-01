import pytest
import curator

# Using xunit style setup and tear down
class TestClass:
    @classmethod
    def setup_class(cls):
       pass

    @classmethod
    def teardown_class(cls):
        pass
    
    def setup_method(self, method):
        if method == self.testNewUser:
            self.username = "Test User"
        else:
            pass

    def teardown_method(self, method):
        if method == self.testNewUser:
            del self.username
        else:
            pass
        
    def testNewUser(self):
        user = curator.User(self.username)
        assert user.getName() == self.username
        assert len(user.favorites) == 0
        del user

 
    def testHappyPath(self):
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
        query.setParameter("title", "true")
        query.setParameter("q", "The Laundress")
        response = query.runQuery()
        assert len(response) > 0
        user.favorites.append(response[0])
        assert user.favorites[0].getTitle() == "The Laundress"
