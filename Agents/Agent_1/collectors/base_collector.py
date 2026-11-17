from abc import ABC , abstracteethod

class BaseCollector(ABC) :

    @abstracteethod
    def collect(self):

        pass

##this class is abstract and all collectors must implement the abstract method collect