"""Unit tests: BACKWARD compatibility rules."""
from app.compatibility import check_backward
from app.schemas import SchemaDefinition


def s(fields):
    return SchemaDefinition(fields=fields)


BASE = s([
    {"name": "id", "type": "string", "required": True},
    {"name": "amount", "type": "int", "required": False},
])


def test_identical_schema_is_compatible():
    breaking, safe = check_backward(BASE, BASE)
    assert not breaking and not safe


def test_adding_optional_field_is_safe():
    new = s([*BASE.model_dump()["fields"],
             {"name": "note", "type": "string", "required": False}])
    breaking, safe = check_backward(BASE, new)
    assert not breaking
    assert any("added optional field 'note'" in m for m in safe)


def test_adding_required_field_breaks():
    new = s([*BASE.model_dump()["fields"],
             {"name": "region", "type": "string", "required": True}])
    breaking, _ = check_backward(BASE, new)
    assert any("required" in m for m in breaking)


def test_removing_field_breaks():
    new = s([{"name": "id", "type": "string", "required": True}])
    breaking, _ = check_backward(BASE, new)
    assert any("removed" in m for m in breaking)


def test_type_narrowing_breaks_but_widening_is_safe():
    widened = s([
        {"name": "id", "type": "string", "required": True},
        {"name": "amount", "type": "double", "required": False},
    ])
    breaking, safe = check_backward(BASE, widened)
    assert not breaking
    assert any("widened" in m for m in safe)

    narrowed = s([
        {"name": "id", "type": "int", "required": True},
        {"name": "amount", "type": "int", "required": False},
    ])
    breaking, _ = check_backward(BASE, narrowed)
    assert any("changed type" in m for m in breaking)


def test_optional_becoming_required_breaks():
    new = s([
        {"name": "id", "type": "string", "required": True},
        {"name": "amount", "type": "int", "required": True},
    ])
    breaking, _ = check_backward(BASE, new)
    assert any("became required" in m for m in breaking)
