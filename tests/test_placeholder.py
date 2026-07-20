"""
Day 3 placeholder test. Deliberately small — the point is to prove the CI
pipeline actually runs pytest and fails on a real failure, not to have
meaningful test coverage yet (that comes once there's real app logic).

Still, a bare `assert True` proves nothing about the pipeline actually
working, so this checks something real and cheap: that yesterday's models
import cleanly and have the table names we expect.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "gateway"))

from models import Unit, Conversation  # noqa: E402


def test_unit_table_name():
    assert Unit.__tablename__ == "units"


def test_conversation_table_name():
    assert Conversation.__tablename__ == "conversations"


def test_unit_has_expected_columns():
    columns = {c.name for c in Unit.__table__.columns}
    assert {"city", "price", "bedrooms", "unit_type"}.issubset(columns)
