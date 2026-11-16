"""Inicialização da persistência: engine, mapeamentos e tabelas.

Extraído de entrypoints/flask_app.py (refatoração SRP, docs/solid.md): a app
factory do Flask não precisa saber como o banco é montado, só receber uma
fábrica de sessões pronta.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from LactoQC.adapters import orm


def build_session_factory(database_url: str) -> sessionmaker:
    """Cria o engine, ativa todos os mapeamentos, cria as tabelas e devolve a fábrica de sessões."""
    engine = create_engine(database_url)
    orm.start_all_mappers()
    orm.metadata.create_all(engine)
    return sessionmaker(bind=engine)
