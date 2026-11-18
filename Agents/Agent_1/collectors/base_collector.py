from abc import ABC , abstractmethod

class BaseCollector(ABC) :

    @abstractmethod
    def collect(self):

        pass

##this class is abstract and all collectors must implement the abstract method collect