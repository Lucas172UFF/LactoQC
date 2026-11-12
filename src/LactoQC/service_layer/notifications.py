"""ConcreteObservers do padrão Observer usado por CollectionPoint (ver docs/gof.md)."""
from __future__ import annotations

import logging

from LactoQC.domain.model import CollectionPoint, NonConformity, NonConformityObserver

logger = logging.getLogger("lactoqc.non_conformities")


class LoggingNonConformityObserver(NonConformityObserver):
    """Registra a não conformidade no log da aplicação.

    Em um deploy real, outro ConcreteObserver poderia enviar e-mail/Slack ao
    supervisor a partir do mesmo evento, sem que o CollectionPoint mude
    (docs/arquitetura.md §5.1, alternativa C).
    """

    def notify(self, collection_point: CollectionPoint, non_conformity: NonConformity) -> None:
        logger.warning(
            "Não conformidade #%s no ponto de coleta %s (%s): %s",
            non_conformity.id_,
            collection_point.id_,
            non_conformity.measurement.measurement_type.name,
            " ".join(non_conformity.description.split()),
        )
