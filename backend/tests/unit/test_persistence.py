"""Transactions and persistence across a new database connection."""

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.db.migrate import apply_schema, enable_sqlite_foreign_keys
from app.db.seed import seed_demo_data
from app.db.transactions import transaction
from app.domain.models import Order, ResolutionCase
from app.schemas.cases import CaseCreateRequest
from app.services.cases import CaseService


def test_transaction_rolls_back_failed_write(db):
    before = db.query(ResolutionCase).count()
    with pytest.raises(IntegrityError):
        with transaction(db):
            db.add(
                ResolutionCase(
                    id="case-bad-fk",
                    user_id="demo-user-1",
                    order_id="missing-order",
                    order_item_id="item-headphones",
                    issue_type="unwanted",
                    issue_description="should roll back",
                    status="open",
                )
            )
    assert db.query(ResolutionCase).count() == before
    assert db.get(ResolutionCase, "case-bad-fk") is None


def test_case_survives_engine_restart(tmp_path: Path):
    url = f"sqlite:///{tmp_path / 'restart.db'}"
    engine = create_engine(url, future=True, connect_args={"check_same_thread": False})
    enable_sqlite_foreign_keys(engine)
    apply_schema(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = Session()
    seed_demo_data(session)
    created = CaseService(session).create(
        user_id="demo-user-1",
        request=CaseCreateRequest(
            order_id="ord-headphones",
            order_item_id="item-headphones",
            issue_type="unwanted",
            issue_description="DEMO persist me",
            eligibility_outcome="ELIGIBLE",
        ),
    )
    case_id = created.id
    session.close()
    engine.dispose()

    engine2 = create_engine(url, future=True, connect_args={"check_same_thread": False})
    enable_sqlite_foreign_keys(engine2)
    session2 = sessionmaker(bind=engine2, autoflush=False, autocommit=False, future=True)()
    restored = session2.get(ResolutionCase, case_id)
    assert restored is not None
    assert restored.issue_description == "DEMO persist me"
    assert session2.get(Order, "ord-headphones") is not None
    session2.close()
    engine2.dispose()
