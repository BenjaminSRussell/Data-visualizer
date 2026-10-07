import pytest

from app.datasets import Dataset, _default_order_by, build_safe_where_clause


def test_unknown_filter_column_raises():
    with pytest.raises(ValueError, match="Unknown filter column"):
        build_safe_where_clause({"nope": 1}, allowed_columns=["domain", "url"])


def test_invalid_identifier_raises():
    with pytest.raises(ValueError, match="Invalid filter column"):
        build_safe_where_clause({"domain;drop": 1}, allowed_columns=["domain"])


def test_builds_params():
    clause, params = build_safe_where_clause({"domain": "a.com"}, ["domain", "url"])
    assert "domain = :filter_domain" in clause
    assert params["filter_domain"] == "a.com"


def test_default_order_prefers_id():
    ds = Dataset(name="t", description="", table_name="t", columns=["url", "id"])
    assert _default_order_by(ds) == "id"
