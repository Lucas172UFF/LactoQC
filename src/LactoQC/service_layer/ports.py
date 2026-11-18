"""Contratos de saída usados pelos casos de uso da aplicação."""

from abc import ABC, abstractmethod
from typing import List, Optional, Protocol, runtime_checkable

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


@runtime_checkable
class TransactionCommitter(Protocol):
    """Port mínimo de transação necessário aos casos de uso."""

    def commit(self) -> None:
        ...
