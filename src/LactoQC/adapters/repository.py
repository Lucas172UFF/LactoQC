import abc
from LactoQC.domain.models import CollectionPoint

class AbstractCollectionPointRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, collection_point: CollectionPoint) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, collection_point_id: str) -> CollectionPoint:
        raise NotImplementedError

    @abc.abstractmethod
    def list(self) -> list[CollectionPoint]:
        raise NotImplementedError