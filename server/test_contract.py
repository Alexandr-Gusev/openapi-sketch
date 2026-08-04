import copy
import json
from pathlib import Path

import yaml
from deepdiff import DeepDiff

from main import app as real_app
from generated.main import app as generated_app

SPEC_PATH = Path(__file__).resolve().parents[1] / "openapi.yml"
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}


def _load_source_spec() -> dict:
    with SPEC_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def apply_security_from_source(spec: dict, source_spec: dict) -> dict:
    patched = copy.deepcopy(spec)
    patched.setdefault("components", {})
    patched["components"]["securitySchemes"] = copy.deepcopy(
        source_spec["components"]["securitySchemes"]
    )

    for path, path_item in source_spec.get("paths", {}).items():
        if path not in patched.get("paths", {}):
            continue
        for method, operation in path_item.items():
            if method not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            if method not in patched["paths"][path]:
                continue
            target = patched["paths"][path][method]
            security = operation.get("security", source_spec.get("security"))
            if security:
                target["security"] = copy.deepcopy(security)

    return patched


def test_contract():
    source_spec = _load_source_spec()
    real_spec = real_app.openapi()
    generated_spec = apply_security_from_source(
        generated_app.openapi(),
        source_spec,
    )

    with open("real_spec.json", "w", encoding="utf-8") as f:
        json.dump(real_spec, f, indent=2, sort_keys=True, ensure_ascii=False)
    with open("generated_spec.json", "w", encoding="utf-8") as f:
        json.dump(generated_spec, f, indent=2, sort_keys=True, ensure_ascii=False)

    diff = DeepDiff(real_spec, generated_spec, ignore_order=True)
    assert not diff, f"diff:\n{diff.pretty()}"
