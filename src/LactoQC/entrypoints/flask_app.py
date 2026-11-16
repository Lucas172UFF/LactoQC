"""Aplicação Flask (app factory), sessão por requisição e tratamento de erros."""
from __future__ import annotations

import os

from flask import Blueprint, Flask, current_app, g, jsonify
from sqlalchemy.orm import Session, sessionmaker

from LactoQC.adapters.database import build_session_factory
from LactoQC.adapters.repository import AbstractRepositoryFactory, SqlAlchemyRepositoryFactory

DEFAULT_DATABASE_URL = "sqlite:///lactoqc.db"


def get_session() -> Session:
    """Sessão da requisição atual. Usar dentro dos endpoints."""
    if "session" not in g:
        g.session = current_app.config["SESSION_FACTORY"]()
    return g.session


def get_repositories() -> AbstractRepositoryFactory:
    """Fábrica de repositórios (Abstract Factory) configurada na aplicação."""
    return current_app.config["REPOSITORY_FACTORY"]


def create_app(
    session_factory: sessionmaker | None = None,
    repository_factory: AbstractRepositoryFactory | None = None,
) -> Flask:
    """Monta a aplicação web. A persistência é montada em adapters/database.py;
    nos testes a session_factory é recebida pronta."""
    app = Flask(__name__)

    if session_factory is None:
        session_factory = build_session_factory(
            os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
        )

    app.config["SESSION_FACTORY"] = session_factory
    app.config["REPOSITORY_FACTORY"] = repository_factory or SqlAlchemyRepositoryFactory()

    @app.teardown_appcontext
    def close_session(_exc):
        session = g.pop("session", None)
        if session is not None:
            session.close()

    _register_error_handlers(app)
    _register_blueprints(app)
    return app


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify(erro="requisição inválida", detalhe=getattr(e, "description", str(e))), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify(erro="não encontrado", detalhe=getattr(e, "description", str(e))), 404

    # Exceções de domínio: ValueError = regra violada (422); LookupError = inexistente (404).
    @app.errorhandler(LookupError)
    def lookup_error(e):
        return jsonify(erro="não encontrado", detalhe=str(e)), 404

    @app.errorhandler(ValueError)
    def domain_error(e):
        return jsonify(erro="regra de negócio violada", detalhe=str(e)), 422


def _register_blueprints(app: Flask) -> None:
    health = Blueprint("health", __name__)

    @health.get("/health")
    def health_check():
        return jsonify(status="ok"), 200

    app.register_blueprint(health)

    from LactoQC.entrypoints.collection_point_routes import bp as collection_point_bp
    from LactoQC.entrypoints.production_batch_routes import bp as production_batch_bp

    app.register_blueprint(collection_point_bp)
    app.register_blueprint(production_batch_bp)

    # TODO: blueprints de Recebimento (Lucas) e Lote de Produção (Aloysio).


if __name__ == "__main__":
    create_app().run(debug=True)
