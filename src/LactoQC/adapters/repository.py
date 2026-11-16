from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy.orm import Session

from LactoQC.domain.model import CollectionPoint, ProductionBatch


class AbstractCollectionPointRepository(ABC):

    @abstractmethod
    def add(self, collection_point: CollectionPoint) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, id_: int) -> Optional[CollectionPoint]:
        raise NotImplementedError

    @abstractmethod
    def list(self) -> List[CollectionPoint]:
        raise NotImplementedError


class SqlAlchemyCollectionPointRepository(AbstractCollectionPointRepository):

    def __init__(self, session: Session):
        self.session = session

    def add(self, collection_point: CollectionPoint) -> None:
        self.session.add(collection_point)

    def get(self, id_: int) -> Optional[CollectionPoint]:
        return self.session.get(CollectionPoint, id_)

    def list(self) -> List[CollectionPoint]:
        return (
            self.session.query(CollectionPoint)
            .order_by(CollectionPoint.id_)
            .all()
        )


class FakeCollectionPointRepository(AbstractCollectionPointRepository):
    """Repositório em memória (antes em tests/conftest.py); simula o autoincremento do banco."""

    def __init__(self):
        self._collection_points = {}
        self._next_id = 1

    def add(self, collection_point: CollectionPoint) -> None:
        if collection_point.id_ is None:
            collection_point.id_ = self._next_id
        self._next_id = max(self._next_id, collection_point.id_ + 1)
        self._collection_points[collection_point.id_] = collection_point

    def get(self, id_: int) -> Optional[CollectionPoint]:
        return self._collection_points.get(id_)

    def list(self) -> List[CollectionPoint]:
        return list(self._collection_points.values())


class AbstractProductionBatchRepository(ABC):

    @abstractmethod
    def add(self, batch: ProductionBatch) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, batch_number: str) -> Optional[ProductionBatch]:
        raise NotImplementedError

    @abstractmethod
    def list(self) -> List[ProductionBatch]:
        raise NotImplementedError


class SqlAlchemyProductionBatchRepository(AbstractProductionBatchRepository):

    def __init__(self, session: Session):
        self.session = session

    def add(self, batch: ProductionBatch) -> None:
        self.session.add(batch)

    def get(self, batch_number: str) -> Optional[ProductionBatch]:
        return (
            self.session.query(ProductionBatch)
            .filter_by(batch_number=batch_number)
            .first()
        )

    def list(self) -> List[ProductionBatch]:
        return self.session.query(ProductionBatch).all()


class FakeProductionBatchRepository(AbstractProductionBatchRepository):

    def __init__(self, batches: Optional[List[ProductionBatch]] = None):
        self._batches = set(batches) if batches else set()

    def add(self, batch: ProductionBatch) -> None:
        self._batches.add(batch)

    def get(self, batch_number: str) -> Optional[ProductionBatch]:
        return next(
            (b for b in self._batches if b.batch_number == batch_number),
            None,
        )

    def list(self) -> List[ProductionBatch]:
        return list(self._batches)


# --- Padrão GoF Abstract Factory (docs/gof.md) -----------------------------
# Família de produtos: um repositório por agregado. Cada fábrica concreta cria
# a família inteira de uma mesma "tecnologia", para que as rotas nunca misturem
# um repositório SQLAlchemy com um em memória nem conheçam as classes concretas.


class AbstractRepositoryFactory(ABC):
    """AbstractFactory: cria os repositórios de todos os agregados."""

    @abstractmethod
    def collection_points(self, session) -> AbstractCollectionPointRepository:
        raise NotImplementedError

    @abstractmethod
    def production_batches(self, session) -> AbstractProductionBatchRepository:
        raise NotImplementedError


class SqlAlchemyRepositoryFactory(AbstractRepositoryFactory):
    """ConcreteFactory de produção: repositórios sobre a sessão da requisição."""

    def collection_points(self, session: Session) -> AbstractCollectionPointRepository:
        return SqlAlchemyCollectionPointRepository(session)

    def production_batches(self, session: Session) -> AbstractProductionBatchRepository:
        return SqlAlchemyProductionBatchRepository(session)


class InMemoryRepositoryFactory(AbstractRepositoryFactory):
    """ConcreteFactory em memória: os mesmos repositórios valem para todas as
    requisições da aplicação, simulando um banco que persiste entre chamadas."""

    def __init__(self):
        self._collection_points = FakeCollectionPointRepository()
        self._production_batches = FakeProductionBatchRepository()

    def collection_points(self, session) -> AbstractCollectionPointRepository:
        return self._collection_points

    def production_batches(self, session) -> AbstractProductionBatchRepository:
        return self._production_batches
