from abc import ABC, abstractmethod, abstractproperty

class AWSResourceInterface(ABC):

    @abstractproperty
    def id(self: object) -> str:
        pass

    @abstractmethod
    def drop(self: object) -> None:
        pass
