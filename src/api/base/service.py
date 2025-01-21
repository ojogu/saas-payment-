#the base service
from abc import ABC, abstractmethod


class BaseService(ABC):
    @abstractmethod
    def create(self):
        pass
    
    @abstractmethod
    def fetch_all():
        """
        Retrieve all resources in the application.

        This abstract method should be implemented by subclasses to handle
        the retrieval of all resources in the application. The method should
        return a list of all the resources in the application. If no resources
        are found, the method should return an empty list.
        """
        pass
    
    
    @abstractmethod
    def fetch_one(self):
        """
        Retrieve a single resource by its identifier.

        This abstract method should be implemented by subclasses to handle
        the retrieval of a specific resource in the application. The identifier
        of the resource to be retrieved should be provided as an argument in
        the subclass implementations.
        """

        pass
    
    
    @abstractmethod
    def update():
        """
        Update an existing resource.

        This abstract method should be implemented by subclasses to handle
        the update of an existing resource in the application. The specifics
        of the resource to be updated and the update logic should be defined
        in the subclass implementations.
        """

        pass
    
    @abstractmethod
    def delete():
        """
        Delete an existing resource.

        This abstract method should be implemented by subclasses to handle
        the deletion of an existing resource in the application. The specifics
        of the resource to be deleted and the deletion logic should be defined
        in the subclass implementations.
        """

        pass
    
    