import ast
from pathlib import Path

from LactoQC.service_layer.ports import TransactionCommitter


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SERVICE_LAYER_FILES = (
    REPOSITORY_ROOT / "src/LactoQC/service_layer/ports.py",
    REPOSITORY_ROOT / "src/LactoQC/service_layer/services.py",
)


def test_service_layer_does_not_import_adapters_or_sqlalchemy():
    for path in SERVICE_LAYER_FILES:
        tree = ast.parse(path.read_text())
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        imported_modules.update(
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )

        assert not any(
            module == "sqlalchemy" or module.startswith("LactoQC.adapters")
            for module in imported_modules
        ), f"{path.name} imports a persistence detail: {imported_modules}"


def test_fake_session_satisfies_transaction_commit_port(fake_session):
    assert isinstance(fake_session, TransactionCommitter)
