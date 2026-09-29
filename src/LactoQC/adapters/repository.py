import abc
from LactoQC.domain.models import CollectionPoint

class AbstractCollectionPointRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, collection_point: CollectionPoint) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, id_: int) -> CollectionPoint | None:
        raise NotImplementedError

    @abc.abstractmethod
    def list(self) -> list[CollectionPoint]:
        raise NotImplementedError


class SqlAlchemyCollectionPointRepository(AbstractCollectionPointRepository):
    def __init__(self, session):
        self.session = session

    def add(self, collection_point: CollectionPoint) -> None:
        self.session.add(collection_point)

    def get(self, id_: int) -> CollectionPoint | None:
        return self.session.get(CollectionPoint, id_)

    def list(self) -> list[CollectionPoint]:
        return self.session.query(CollectionPoint).order_by(CollectionPoint.id_).all()