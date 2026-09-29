from sqlalchemy import Column, Integer, String, Table
from sqlalchemy.orm import Session, registry

from LactoQC.adapters.repository import SqlAlchemyRepository


class Coisa:
    def __init__(self, nome):
        self.nome = nome


def test_repositorio_generico_add_get_list_find_remove(in_memory_engine):
    # registry próprio, isolado do orm.py, só para testar o repositório genérico
    reg = registry()
    tabela = Table("coisas", reg.metadata, Column("id", Integer, primary_key=True), Column("nome", String))
    reg.map_imperatively(Coisa, tabela)
    reg.metadata.create_all(in_memory_engine)

    with Session(in_memory_engine) as session:
        repo = SqlAlchemyRepository(session, Coisa)
        a, b = Coisa("a"), Coisa("b")
        repo.add(a)
        repo.add(b)
        session.commit()

        assert repo.get(a.id) is a
        assert repo.get(999) is None
        assert len(repo.list()) == 2
        assert repo.find_by(nome="b") == [b]

        repo.remove(a)
        session.commit()
        assert repo.list() == [b]

    reg.dispose()
