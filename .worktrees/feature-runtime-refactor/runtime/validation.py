from typing import Any, Dict


class SchemaValidationError(ValueError):
    pass


def _check_type(expected: str, value: Any) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return True


def validate(data: Any, schema: Dict[str, Any], path: str = "$") -> None:
    expected_type = schema.get("type")
    if expected_type and not _check_type(expected_type, data):
        raise SchemaValidationError(f"{path}: expected {expected_type}, got {type(data).__name__}")
    enum = schema.get("enum")
    if enum is not None and data not in enum:
        raise SchemaValidationError(f"{path}: value {data!r} not in enum {enum!r}")
    if expected_type == "object":
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        for name in required:
            if name not in data:
                raise SchemaValidationError(f"{path}: missing required key {name}")
        if schema.get("additionalProperties") is False:
            extra = set(data) - set(properties)
            if extra:
                raise SchemaValidationError(f"{path}: unexpected keys {sorted(extra)!r}")
        for key, value in data.items():
            if key in properties:
                validate(value, properties[key], f"{path}.{key}")
    if expected_type == "array":
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(data):
                validate(item, item_schema, f"{path}[{index}]")
