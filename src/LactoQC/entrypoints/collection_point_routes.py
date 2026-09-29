from __future__ import annotations

from datetime import datetime

from flask import Blueprint, abort, jsonify, request

from LactoQC.adapters.repository import AbstractCollectionPointRepository, SqlAlchemyCollectionPointRepository
from LactoQC.entrypoints.flask_app import get_session
from LactoQC.service_layer import services

bp = Blueprint("collection_points", __name__)


def _repo() -> CollectionPointRepository:
    return CollectionPointRepository(get_session())


def _json_body() -> dict:
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        abort(400, description="JSON object body is required.")
    return body


def _require(body: dict, *fields: str) -> None:
    missing = [f for f in fields if f not in body]
    if missing:
        abort(400, description=f"Missing required field(s): {', '.join(missing)}.")


def _parse_datetime(raw: str | None, field: str) -> datetime | None:
    if raw is None:
        return None
    try:
        return datetime.fromisoformat(raw)
    except (TypeError, ValueError):
        raise ValueError(f"'{field}' must be an ISO 8601 date/time (e.g. 2026-09-29T08:00:00).")


def _spec_json(spec) -> dict:
    return {
        "measurement_type": spec.measurement_type.name,
        "min_value": spec.min_value,
        "max_value": spec.max_value,
        "measurement_unit": spec.measurement_unit.value if spec.measurement_unit else None,
    }


def _measurement_json(m) -> dict:
    return {
        "id": m.id_,
        "measurement_type": m.measurement_type.name,
        "value": m.value,
        "measurement_unit": m.measurement_unit.value if m.measurement_unit else None,
        "measurement_date": m.measurement_date.isoformat(),
    }


def _non_conformity_json(nc) -> dict:
    return {
        "number": nc.id_,
        "collection_point_id": nc.collection_point_id,
        "measurement_id": nc.measurement.id_,
        "measurement_type": nc.measurement.measurement_type.name,
        "value": nc.measurement.value,
        "measurement_date": nc.measurement.measurement_date.isoformat(),
        # A descrição do domínio tem quebras de linha/indentação; normaliza para a API.
        "description": " ".join(nc.description.split()),
    }


def _collection_point_json(cp, detailed: bool = False) -> dict:
    data = {
        "id": cp.id_,
        "name": cp.name,
        "location": cp.location,
        "specifications": [_spec_json(s) for s in cp.specifications],
    }
    if detailed:
        data["measurements"] = [_measurement_json(m) for m in cp.measurements]
        data["non_conformities"] = [_non_conformity_json(n) for n in cp.non_conformities]
    return data


@bp.post("/collection-points")
def create_collection_point():
    body = _json_body()
    _require(body, "name", "location", "specifications")
    if not isinstance(body["specifications"], list):
        abort(400, description="'specifications' must be a list.")
    session = get_session()
    cp = services.create_collection_point(
        CollectionPointRepository(session), session,
        name=body["name"], location=body["location"], specifications=body["specifications"],
    )
    return jsonify(_collection_point_json(cp)), 201


@bp.get("/collection-points/<int:collection_point_id>")
def get_collection_point(collection_point_id: int):
    cp = services.get_collection_point(_repo(), collection_point_id)
    return jsonify(_collection_point_json(cp, detailed=True)), 200


@bp.post("/collection-points/<int:collection_point_id>/measurements")
def register_measurement(collection_point_id: int):
    body = _json_body()
    _require(body, "measurement_type", "value")
    session = get_session()
    measurement, new_ncs = services.register_measurement(
        CollectionPointRepository(session), session, collection_point_id,
        measurement_type=body["measurement_type"], value=body["value"],
        measurement_date=_parse_datetime(body.get("measurement_date"), "measurement_date"),
    )
    return jsonify(
        measurement=_measurement_json(measurement),
        non_conformities=[_non_conformity_json(n) for n in new_ncs],
    ), 201


@bp.get("/non-conformities")
def list_non_conformities():
    cp_id_raw = request.args.get("collection_point_id")
    try:
        cp_id = int(cp_id_raw) if cp_id_raw is not None else None
    except ValueError:
        raise ValueError("'collection_point_id' must be an integer.")
    ncs = services.list_non_conformities(
        _repo(),
        start=_parse_datetime(request.args.get("start"), "start"),
        end=_parse_datetime(request.args.get("end"), "end"),
        collection_point_id=cp_id,
    )
    return jsonify([_non_conformity_json(n) for n in ncs]), 200
