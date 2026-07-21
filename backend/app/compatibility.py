"""BACKWARD schema compatibility: can the new schema read data written
with the old schema? Mirrors the checks a schema registry runs.
"""
from .schemas import SchemaDefinition

# widenings that don't lose information
SAFE_TYPE_WIDENINGS = {
    ("int", "long"), ("int", "float"), ("int", "double"),
    ("long", "double"), ("float", "double"),
}


def check_backward(old: SchemaDefinition, new: SchemaDefinition):
    old_fields = {f.name: f for f in old.fields}
    new_fields = {f.name: f for f in new.fields}
    breaking: list[str] = []
    safe: list[str] = []

    for name, old_f in old_fields.items():
        if name not in new_fields:
            breaking.append(
                f"field '{name}' was removed - existing records still carry it "
                f"and downstream consumers may still read it"
            )
            continue
        new_f = new_fields[name]
        if old_f.type != new_f.type:
            if (old_f.type, new_f.type) in SAFE_TYPE_WIDENINGS:
                safe.append(f"field '{name}' widened {old_f.type} -> {new_f.type}")
            else:
                breaking.append(
                    f"field '{name}' changed type {old_f.type} -> {new_f.type} - "
                    f"old records will fail to parse"
                )
        if not old_f.required and new_f.required:
            breaking.append(
                f"field '{name}' became required - old records without it "
                f"can no longer be read"
            )

    for name, new_f in new_fields.items():
        if name not in old_fields:
            if new_f.required:
                breaking.append(
                    f"new field '{name}' is required - records written before "
                    f"this version don't have it"
                )
            else:
                safe.append(f"added optional field '{name}'")

    return breaking, safe
