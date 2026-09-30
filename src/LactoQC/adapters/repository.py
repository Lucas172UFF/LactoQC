from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy.orm import Session

from LactoQC.domain.model import ProductionBatch


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