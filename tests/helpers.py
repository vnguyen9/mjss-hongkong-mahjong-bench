"""Shared bits for the tests."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hkbench.engine.profile import load_profile  # noqa: E402
from hkbench.tables import load_table  # noqa: E402

_cache = {}


def hkma_profile():
    if "p" not in _cache:
        _cache["p"] = load_profile(ROOT / "tables" / "hk-hkma-v1" / "rules.json")
    return _cache["p"]


def house_profile():
    if "h" not in _cache:
        _cache["h"] = load_profile(ROOT / "tables" / "hk-house-v1" / "rules.json")
    return _cache["h"]


def house_table():
    return load_table("hk-house-v1")


def hkma_table():
    return load_table("hk-hkma-v1")


# --- a small JSON Schema checker (just the keywords protocol/schema.json uses) ---------------

import json  # noqa: E402

SCHEMA = json.loads((ROOT / "protocol" / "schema.json").read_text(encoding="utf-8"))
_TYPES = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float),
          "boolean": bool, "null": type(None)}


def _type_ok(value, name):
    if name == "integer" and isinstance(value, bool):
        return False
    return isinstance(value, _TYPES[name])


def schema_errors(value, schema, path="$"):
    """A list of problems; empty if ``value`` fits ``schema``."""
    errs = []
    if "$ref" in schema:
        node = SCHEMA
        for part in schema["$ref"].lstrip("#/").split("/"):
            node = node[part]
        return schema_errors(value, node, path)
    if "const" in schema and value != schema["const"]:
        errs.append("%s: expected %r" % (path, schema["const"]))
    if "enum" in schema and value not in schema["enum"]:
        errs.append("%s: %r not in %r" % (path, value, schema["enum"]))
    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_type_ok(value, t) for t in types):
            errs.append("%s: %r is not %s" % (path, value, types))
            return errs
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errs.append("%s: %r below %r" % (path, value, schema["minimum"]))
        if "maximum" in schema and value > schema["maximum"]:
            errs.append("%s: %r above %r" % (path, value, schema["maximum"]))
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errs.append("%s: missing %s" % (path, key))
        for key, sub in schema.get("properties", {}).items():
            if key in value:
                errs.extend(schema_errors(value[key], sub, "%s.%s" % (path, key)))
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errs.append("%s: fewer than %d items" % (path, schema["minItems"]))
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errs.append("%s: more than %d items" % (path, schema["maxItems"]))
        if "items" in schema:
            for i, item in enumerate(value):
                errs.extend(schema_errors(item, schema["items"], "%s[%d]" % (path, i)))
    return errs


def check_message(msg, kind):
    return schema_errors(msg, {"$ref": "#/$defs/" + kind})
