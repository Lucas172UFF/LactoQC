from __future__ import annotations

from datetime import datetime

from flask import Blueprint, abort, jsonify, request

from LactoQC.adapters.repository import (
    AbstractProductionBatchRepository,
    SqlAlchemyProductionBatchRepository,
)
from LactoQC.domain.model import (
    BatchStatus,
    RawMaterialReceipt,
    RawMaterialReceiptStatus,
)
from LactoQC.entrypoints.flask_app import get_session
from LactoQC.service_layer import services


bp = Blueprint("production_batches", __name__)


def _repo() -> AbstractProductionBatchRepository:
    return SqlAlchemyProductionBatchRepository(get_session())


def _json_body() -> dict:
    body = request.get_json(silent=True)

    if not isinstance(body, dict):
        abort(400, description="JSON object body is required.")

    return body


def _require(body: dict, *fields: str) -> None:
    missing = [field for field in fields if field not in body]

    if missing:
        abort(
            400,
            description=f"Missing required field(s): {', '.join(missing)}.",
        )


def _parse_datetime(raw: str | None, field: str) -> datetime | None:
    if raw is None:
        return None

    try:
        return datetime.fromisoformat(raw)
    except (TypeError, ValueError):
        raise ValueError(
            f"'{field}' must be an ISO 8601 date/time "
            f"(e.g. 2026-09-30T08:00:00)."
        )


def _parse_raw_material_status(raw: str) -> RawMaterialReceiptStatus:
    if not isinstance(raw, str):
        raise ValueError("'status' must be a string.")

    text = raw.strip()

    if text.upper() in RawMaterialReceiptStatus.__members__:
        return RawMaterialReceiptStatus[text.upper()]

    for status in RawMaterialReceiptStatus:
        if status.value.lower() == text.lower():
            return status

    valid = ", ".join(RawMaterialReceiptStatus.__members__)

    raise ValueError(
        f"Invalid raw material status {raw!r}. Valid statuses: {valid}."
    )


def _production_batch_json(batch, detailed: bool = False) -> dict:
    data = {
        "id": batch.id_,
        "batch_number": batch.batch_number,
        "production_date": batch.production_date.isoformat(),
        "milk_type": batch.milk_type.name,
        "milk_type_label": batch.milk_type.value,
        "expected_weight": batch.expected_weight,
        "wettability_result": batch.wettability_result.name,
        "status": batch.status.name,
        "status_label": batch.status.value,
        "raw_material_receipt": {
            "id": batch.raw_material_receipt.id_,
            "status": batch.raw_material_receipt.status.name,
            "status_label": batch.raw_material_receipt.status.value,
        },
    }

    if detailed:
        data["weight_samples"] = [
            {
                "id": sample.id_,
                "date_time": sample.date_time.isoformat(),
                "weight_kg": sample.weight_kg,
            }
            for sample in batch.weight_samples
        ]

        data["lecithinization"] = (
            {
                "performed": batch.lecithinization.performed,
                "date_time": (
                    batch.lecithinization.date_time.isoformat()
                    if batch.lecithinization.date_time
                    else None
                ),
                "responsible": batch.lecithinization.responsible,
            }
            if batch.lecithinization
            else None
        )

        data["non_conformities"] = [
            {
                "id": nc.id_,
                "batch_id": nc.batch_id,
                "description": nc.description,
            }
            for nc in batch.non_conformities
        ]

    return data


def _non_conformity_json(nc) -> dict:
    return {
        "id": nc.id_,
        "batch_id": nc.batch_id,
        "description": nc.description,
    }


@bp.post("/production-batches")
def create_production_batch():
    body = _json_body()

    _require(
        body,
        "batch_number",
        "production_date",
        "milk_type",
        "raw_material_receipt",
        "expected_weight",
    )

    if not isinstance(body["raw_material_receipt"], dict):
        abort(
            400,
            description="'raw_material_receipt' must be an object.",
        )

    receipt_data = body["raw_material_receipt"]

    if "id" not in receipt_data or "status" not in receipt_data:
        abort(
            400,
            description="Raw material receipt requires 'id' and 'status'.",
        )

    production_date = _parse_datetime(
        body["production_date"],
        "production_date",
    )

    receipt_status = _parse_raw_material_status(
        receipt_data["status"]
    )

    raw_material_receipt = RawMaterialReceipt(
        id_=receipt_data["id"],
        status=receipt_status,
    )

    session = get_session()

    batch = services.create_production_batch(
        SqlAlchemyProductionBatchRepository(session),
        session,
        batch_number=body["batch_number"],
        production_date=production_date,
        milk_type=body["milk_type"],
        raw_material_receipt=raw_material_receipt,
        expected_weight=body["expected_weight"],
    )

    return jsonify(_production_batch_json(batch, detailed=True)), 201


@bp.get("/production-batches")
def list_production_batches():
    batches = services.list_production_batches(_repo())

    return jsonify(
        [_production_batch_json(batch) for batch in batches]
    ), 200


@bp.get("/production-batches/<batch_number>")
def get_production_batch(batch_number: str):
    batch = services.get_production_batch(
        _repo(),
        batch_number,
    )

    return jsonify(
        _production_batch_json(batch, detailed=True)
    ), 200


@bp.post("/production-batches/<batch_number>/weight-samples")
def register_weight_sample(batch_number: str):
    body = _json_body()

    _require(body, "weight_kg")

    session = get_session()

    sample, new_ncs = services.register_weight_sample(
        SqlAlchemyProductionBatchRepository(session),
        session,
        batch_number=batch_number,
        weight_kg=body["weight_kg"],
        date_time=_parse_datetime(
            body.get("date_time"),
            "date_time",
        ),
    )

    return jsonify(
        weight_sample={
            "id": sample.id_,
            "date_time": sample.date_time.isoformat(),
            "weight_kg": sample.weight_kg,
        },
        non_conformities=[
            _non_conformity_json(nc)
            for nc in new_ncs
        ],
    ), 201


@bp.post("/production-batches/<batch_number>/lecithinization")
def register_lecithinization(batch_number: str):
    body = _json_body()

    _require(body, "performed")

    if not isinstance(body["performed"], bool):
        abort(
            400,
            description="'performed' must be a boolean.",
        )

    session = get_session()

    lecithinization = services.register_lecithinization(
        SqlAlchemyProductionBatchRepository(session),
        session,
        batch_number=batch_number,
        performed=body["performed"],
        date_time=_parse_datetime(
            body.get("date_time"),
            "date_time",
        ),
        responsible=body.get("responsible"),
    )

    return jsonify(
        lecithinization={
            "performed": lecithinization.performed,
            "date_time": (
                lecithinization.date_time.isoformat()
                if lecithinization.date_time
                else None
            ),
            "responsible": lecithinization.responsible,
        }
    ), 201


@bp.post("/production-batches/<batch_number>/wettability")
def register_wettability_result(batch_number: str):
    body = _json_body()

    _require(body, "result")

    session = get_session()

    result, new_ncs = services.register_wettability_result(
        SqlAlchemyProductionBatchRepository(session),
        session,
        batch_number=batch_number,
        result=body["result"],
    )

    return jsonify(
        result=result.name,
        result_label=result.value,
        non_conformities=[
            _non_conformity_json(nc)
            for nc in new_ncs
        ],
    ), 201


@bp.post("/production-batches/<batch_number>/release")
def release_production_batch(batch_number: str):
    session = get_session()

    batch, new_ncs = services.release_production_batch(
        SqlAlchemyProductionBatchRepository(session),
        session,
        batch_number,
    )

    return jsonify(
        batch=_production_batch_json(batch, detailed=True),
        non_conformities=[
            _non_conformity_json(nc)
            for nc in new_ncs
        ],
    ), 200