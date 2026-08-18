#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pyyaml>=6.0,<7",
# ]
# ///

"""Validate a compact Architecture Guardian project state.

Usage:
  uv run validate_architecture.py <architecture-dir>
  uv run validate_architecture.py --strict <architecture-dir>

Default mode reports incomplete/placeholder state as warnings where possible.
Strict mode promotes unresolved references and placeholders to errors for CI/bootstrap use.
The validator checks objective structure only; it does not replace architecture judgment.
"""
from __future__ import annotations

import sys
import re
from pathlib import Path
from typing import Any

import yaml


PLACEHOLDER_MARKERS = ("replace-me", "replace with", "todo", "tbd")


class Report:
    def __init__(self, strict: bool = False) -> None:
        self.strict = strict
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str, strict_error: bool = False) -> None:
        if self.strict and strict_error:
            self.errors.append(message)
        else:
            self.warnings.append(message)


def load_yaml(path: Path, report: Report, required: bool = True) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        if required:
            report.error(f"Missing required file: {path}")
        return None
    except yaml.YAMLError as exc:
        report.error(f"Invalid YAML in {path}: {exc}")
        return None
    scan_placeholders(data, str(path), report)
    return data


def scan_placeholders(value: Any, label: str, report: Report) -> None:
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in PLACEHOLDER_MARKERS):
            report.warn(f"Placeholder content in {label}: {value!r}", strict_error=True)
    elif isinstance(value, list):
        for item in value:
            scan_placeholders(item, label, report)
    elif isinstance(value, dict):
        for item in value.values():
            scan_placeholders(item, label, report)


def require_keys(obj: Any, keys: list[str], label: str, report: Report) -> None:
    if not isinstance(obj, dict):
        report.error(f"{label} must be a mapping")
        return
    for key in keys:
        if key not in obj:
            report.error(f"{label} missing required key: {key}")


def iter_yaml(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted([*directory.glob("*.yaml"), *directory.glob("*.yml")])


def path_from_repo(repo_root: Path, value: Any, label: str, report: Report) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        report.error(f"{label} must be a non-empty relative path")
        return None
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        report.error(f"{label} must stay inside the repository: {value}")
        return None
    resolved = (repo_root / candidate).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        report.error(f"{label} resolves outside the repository: {value}")
        return None
    if not resolved.exists():
        report.error(f"Missing path for {label}: {value}")
        return None
    return resolved


def validate_path_list(
    values: Any,
    label: str,
    repo_root: Path,
    report: Report,
    must_be_test: bool = False,
) -> list[str]:
    if not isinstance(values, list):
        report.error(f"{label} must be a list")
        return []
    valid: list[str] = []
    for index, value in enumerate(values):
        path = path_from_repo(repo_root, value, f"{label}[{index}]", report)
        if path is None:
            continue
        normalized = Path(value).as_posix()
        if must_be_test and not normalized.startswith("src/test/"):
            report.error(f"{label}[{index}] must be under src/test/: {value}")
        valid.append(normalized)
    return valid


def validate_packages(packages: Any, label: str, repo_root: Path, report: Report) -> None:
    if not isinstance(packages, list):
        report.error(f"{label} must be a list")
        return
    for index, package in enumerate(packages):
        if not isinstance(package, str) or not package.strip():
            report.error(f"{label}[{index}] must be a non-empty package name")
            continue
        package_path = Path("src/main/java", *package.split("."))
        path_from_repo(repo_root, package_path.as_posix(), f"{label}[{index}]", report)


def validate_java_symbol(symbol: Any, label: str, repo_root: Path, report: Report) -> str | None:
    if not isinstance(symbol, str) or not symbol.strip():
        report.error(f"{label} must be a non-empty Java symbol")
        return None
    class_name, separator, method_name = symbol.partition("#")
    if not re.fullmatch(r"[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*", class_name):
        report.error(f"Invalid Java symbol in {label}: {symbol}")
        return None
    class_path = repo_root / "src/main/java" / Path(*class_name.split("."))
    class_path = class_path.with_suffix(".java")
    if not class_path.is_file():
        report.error(f"Missing Java source for {label}: {class_path.relative_to(repo_root)}")
        return None
    source = class_path.read_text(encoding="utf-8")
    simple_name = class_name.rsplit(".", 1)[-1]
    if not re.search(rf"\b(?:class|interface|record|enum)\s+{re.escape(simple_name)}\b", source):
        report.error(f"Java type {class_name} is not declared in {class_path.relative_to(repo_root)}")
    if separator:
        if not method_name or not re.search(rf"\b{re.escape(method_name)}\s*\(", source):
            report.error(f"Java method {symbol} is not found in {class_path.relative_to(repo_root)}")
    return symbol


def validate_implementation(
    implementation: Any,
    root: Path,
    module_names: set[str],
    report: Report,
) -> set[str]:
    require_keys(implementation, ["schema_version", "boundaries"], "implementation.yaml", report)
    symbols: set[str] = set()
    if not isinstance(implementation, dict):
        return symbols
    boundaries = implementation.get("boundaries", [])
    if not isinstance(boundaries, list):
        report.error("implementation.yaml: boundaries must be a list")
        return symbols
    seam_ids: set[str] = set()
    repo_root = root.parent
    for boundary_index, boundary in enumerate(boundaries):
        label = f"implementation.yaml: boundaries[{boundary_index}]"
        require_keys(boundary, ["boundary", "seams"], label, report)
        if not isinstance(boundary, dict):
            continue
        boundary_name = boundary.get("boundary")
        if boundary_name not in module_names:
            report.error(f"{label}.boundary is not a declared module: {boundary_name}")
        seams = boundary.get("seams", [])
        if not isinstance(seams, list):
            report.error(f"{label}.seams must be a list")
            continue
        for seam_index, seam in enumerate(seams):
            seam_label = f"{label}.seams[{seam_index}]"
            require_keys(seam, ["id", "kind", "packages", "source_files", "symbols", "test_paths"], seam_label, report)
            if not isinstance(seam, dict):
                continue
            seam_id = seam.get("id")
            if not isinstance(seam_id, str) or not seam_id.strip():
                report.error(f"{seam_label}.id must be a non-empty string")
            elif seam_id in seam_ids:
                report.error(f"Duplicate implementation seam id: {seam_id}")
            else:
                seam_ids.add(seam_id)
            validate_packages(seam.get("packages"), f"{seam_label}.packages", repo_root, report)
            validate_path_list(seam.get("source_files"), f"{seam_label}.source_files", repo_root, report)
            validate_path_list(seam.get("test_paths"), f"{seam_label}.test_paths", repo_root, report, must_be_test=True)
            seam_symbols = seam.get("symbols", [])
            if not isinstance(seam_symbols, list):
                report.error(f"{seam_label}.symbols must be a list")
            else:
                for symbol_index, symbol in enumerate(seam_symbols):
                    valid_symbol = validate_java_symbol(symbol, f"{seam_label}.symbols[{symbol_index}]", repo_root, report)
                    if valid_symbol:
                        symbols.add(valid_symbol)
            if "shared_hotspots" in seam:
                shared_hotspots = seam.get("shared_hotspots")
                if not isinstance(shared_hotspots, list) or any(
                    not isinstance(hotspot, str) or not hotspot.strip() for hotspot in shared_hotspots
                ):
                    report.error(f"{seam_label}.shared_hotspots must be a list of hotspot ids")
    return symbols


def validate_work_units(
    work_units_doc: Any,
    root: Path,
    module_names: set[str],
    contract_names: set[str],
    invariant_ids: set[str],
    implementation_symbols: set[str],
    report: Report,
) -> tuple[int, int]:
    require_keys(work_units_doc, ["schema_version", "shared_hotspots", "work_units"], "work-units.yaml", report)
    if not isinstance(work_units_doc, dict):
        return 0, 0
    repo_root = root.parent
    hotspot_ids: set[str] = set()
    hotspot_owners: dict[str, str] = {}
    hotspots = work_units_doc.get("shared_hotspots", [])
    if not isinstance(hotspots, list):
        report.error("work-units.yaml: shared_hotspots must be a list")
    else:
        for index, hotspot in enumerate(hotspots):
            label = f"work-units.yaml: shared_hotspots[{index}]"
            require_keys(hotspot, ["id", "path", "owner_work_unit", "reason"], label, report)
            if not isinstance(hotspot, dict):
                continue
            hotspot_id = hotspot.get("id")
            if not isinstance(hotspot_id, str) or not hotspot_id.strip():
                report.error(f"{label}.id must be a non-empty string")
            elif hotspot_id in hotspot_ids:
                report.error(f"Duplicate shared hotspot id: {hotspot_id}")
            else:
                hotspot_ids.add(hotspot_id)
            path_from_repo(repo_root, hotspot.get("path"), f"{label}.path", report)
            owner = hotspot.get("owner_work_unit")
            if isinstance(hotspot_id, str) and isinstance(owner, str):
                hotspot_owners[hotspot_id] = owner

    units = work_units_doc.get("work_units", [])
    if not isinstance(units, list):
        report.error("work-units.yaml: work_units must be a list")
        return len(hotspot_ids), 0
    unit_ids: set[str] = set()
    unit_may_change: dict[str, set[str]] = {}
    for index, unit in enumerate(units):
        label = f"work-units.yaml: work_units[{index}]"
        require_keys(
            unit,
            ["id", "label", "owner_boundary", "parallelism", "purpose", "may_change", "must_not_change",
             "implementation_symbols", "test_paths", "contracts", "invariants", "shared_hotspots", "completion"],
            label,
            report,
        )
        if not isinstance(unit, dict):
            continue
        unit_id = unit.get("id")
        if not isinstance(unit_id, str) or not unit_id.strip():
            report.error(f"{label}.id must be a non-empty string")
            continue
        if unit_id in unit_ids:
            report.error(f"Duplicate work unit id: {unit_id}")
        unit_ids.add(unit_id)
        if unit.get("owner_boundary") not in module_names:
            report.error(f"{label}.owner_boundary is not a declared module: {unit.get('owner_boundary')}")
        may_change = set(validate_path_list(unit.get("may_change"), f"{label}.may_change", repo_root, report))
        must_not_change = set(validate_path_list(unit.get("must_not_change"), f"{label}.must_not_change", repo_root, report))
        overlap = may_change & must_not_change
        for path in sorted(overlap):
            report.error(f"{label} path is both may_change and must_not_change: {path}")
        unit_may_change[unit_id] = may_change
        validate_path_list(unit.get("test_paths"), f"{label}.test_paths", repo_root, report, must_be_test=True)
        symbols = unit.get("implementation_symbols", [])
        if not isinstance(symbols, list):
            report.error(f"{label}.implementation_symbols must be a list")
        else:
            for symbol in symbols:
                if symbol not in implementation_symbols:
                    report.error(f"{label} references unmapped implementation symbol: {symbol}")
        contracts = unit.get("contracts", [])
        if not isinstance(contracts, list):
            report.error(f"{label}.contracts must be a list")
        else:
            for contract in contracts:
                if contract not in contract_names:
                    report.error(f"{label} references unknown contract: {contract}")
        invariants = unit.get("invariants", [])
        if not isinstance(invariants, list):
            report.error(f"{label}.invariants must be a list")
        else:
            for invariant in invariants:
                if invariant not in invariant_ids:
                    report.error(f"{label} references unknown invariant: {invariant}")
        shared = unit.get("shared_hotspots", [])
        if not isinstance(shared, list):
            report.error(f"{label}.shared_hotspots must be a list")
        else:
            for hotspot in shared:
                if hotspot not in hotspot_ids:
                    report.error(f"{label} references unknown shared hotspot: {hotspot}")
        completion = unit.get("completion")
        require_keys(completion, ["required_checks", "acceptance"], f"{label}.completion", report)
        if isinstance(completion, dict):
            for key in ("required_checks", "acceptance"):
                if not isinstance(completion.get(key), list) or not completion.get(key):
                    report.error(f"{label}.completion.{key} must be a non-empty list")

    for hotspot_id, owner in hotspot_owners.items():
        if owner not in unit_ids:
            report.error(f"Shared hotspot '{hotspot_id}' owner is not a work unit: {owner}")
        else:
            hotspot_path = next(
                (hotspot.get("path") for hotspot in hotspots if isinstance(hotspot, dict) and hotspot.get("id") == hotspot_id),
                None,
            )
            if hotspot_path not in unit_may_change.get(owner, set()):
                report.error(f"Shared hotspot '{hotspot_id}' path is not owned by {owner}: {hotspot_path}")

    paths_to_units: dict[str, list[str]] = {}
    for unit_id, paths in unit_may_change.items():
        for path in paths:
            paths_to_units.setdefault(path, []).append(unit_id)
    for path, owners in sorted(paths_to_units.items()):
        if len(owners) > 1:
            report.error(f"may_change path is assigned to multiple work units: {path} -> {', '.join(sorted(owners))}")
    return len(hotspot_ids), len(unit_ids)


def parse_args() -> tuple[bool, Path] | None:
    args = sys.argv[1:]
    strict = False
    if args and args[0] == "--strict":
        strict = True
        args = args[1:]
    if len(args) != 1:
        print("Usage: validate_architecture.py [--strict] <architecture-dir>", file=sys.stderr)
        return None
    return strict, Path(args[0]).resolve()


def main() -> int:
    parsed = parse_args()
    if parsed is None:
        return 2
    strict, root = parsed
    report = Report(strict=strict)

    if not root.is_dir():
        print(f"ERROR: not a directory: {root}", file=sys.stderr)
        return 2

    constitution = load_yaml(root / "constitution.yaml", report)
    system = load_yaml(root / "system.yaml", report)
    invariants_doc = load_yaml(root / "invariants.yaml", report)
    load_yaml(root / "glossary.yaml", report, required=False)
    load_yaml(root / "evolution.yaml", report, required=False)
    implementation_doc = load_yaml(root / "implementation.yaml", report)
    work_units_doc = load_yaml(root / "work-units.yaml", report)

    require_keys(constitution, ["version", "principles", "hard_rules"], "constitution.yaml", report)
    require_keys(system, ["name", "goals", "quality_attributes"], "system.yaml", report)
    require_keys(invariants_doc, ["invariants"], "invariants.yaml", report)

    module_names: set[str] = set()
    ownership: dict[str, str] = {}
    module_files = iter_yaml(root / "modules")
    if not module_files:
        report.warn("No boundary/module files found in architecture/modules/")

    for path in module_files:
        mod = load_yaml(path, report)
        require_keys(
            mod,
            ["name", "purpose", "owns", "public_api", "dependencies", "forbidden_dependencies"],
            str(path.relative_to(root)),
            report,
        )
        if not isinstance(mod, dict):
            continue
        name = mod.get("name")
        if not isinstance(name, str) or not name.strip():
            report.error(f"{path.name}: name must be a non-empty string")
            continue
        if name in module_names:
            report.error(f"Duplicate boundary/module name: {name}")
        module_names.add(name)

        owns = mod.get("owns", [])
        if not isinstance(owns, list):
            report.error(f"{path.name}: owns must be a list")
        else:
            for concept in owns:
                if not isinstance(concept, str):
                    report.error(f"{path.name}: ownership entries must be strings")
                    continue
                previous = ownership.get(concept)
                if previous and previous != name:
                    report.error(f"Duplicate authoritative ownership for '{concept}': {previous}, {name}")
                else:
                    ownership[concept] = name

        deps = mod.get("dependencies", [])
        forbidden = mod.get("forbidden_dependencies", [])
        if not isinstance(deps, list):
            report.error(f"{path.name}: dependencies must be a list")
        if not isinstance(forbidden, list):
            report.error(f"{path.name}: forbidden_dependencies must be a list")
        if isinstance(deps, list) and isinstance(forbidden, list):
            overlap = {d for d in deps if isinstance(d, str)} & {d for d in forbidden if isinstance(d, str)}
            for dep in sorted(overlap):
                report.error(f"{path.name}: dependency '{dep}' is both allowed and forbidden")

    invariant_ids: set[str] = set()
    invariant_owners: list[tuple[str, str]] = []
    if isinstance(invariants_doc, dict):
        invs = invariants_doc.get("invariants", [])
        if not isinstance(invs, list):
            report.error("invariants.yaml: invariants must be a list")
        else:
            for i, inv in enumerate(invs):
                label = f"invariants.yaml: invariants[{i}]"
                require_keys(inv, ["id", "statement", "owner"], label, report)
                if not isinstance(inv, dict):
                    continue
                inv_id = inv.get("id")
                owner = inv.get("owner")
                if isinstance(inv_id, str):
                    if inv_id in invariant_ids:
                        report.error(f"Duplicate invariant id: {inv_id}")
                    invariant_ids.add(inv_id)
                if isinstance(inv_id, str) and isinstance(owner, str):
                    invariant_owners.append((inv_id, owner))

    contract_names: set[str] = set()
    for path in iter_yaml(root / "contracts"):
        contract = load_yaml(path, report)
        require_keys(contract, ["name", "provider", "consumers", "operations"], str(path.relative_to(root)), report)
        if not isinstance(contract, dict):
            continue
        name = contract.get("name")
        if not isinstance(name, str) or not name.strip():
            report.error(f"{path.name}: contract name must be a non-empty string")
            continue
        if name in contract_names:
            report.error(f"Duplicate contract name: {name}")
        contract_names.add(name)

        provider = contract.get("provider")
        if isinstance(provider, str) and module_names and provider not in module_names:
            report.warn(f"{path.name}: provider '{provider}' is not a declared boundary/module", strict_error=True)
        consumers = contract.get("consumers", [])
        if not isinstance(consumers, list):
            report.error(f"{path.name}: consumers must be a list")
        elif module_names:
            for consumer in consumers:
                if isinstance(consumer, str) and consumer not in module_names:
                    report.warn(f"{path.name}: consumer '{consumer}' is not a declared boundary/module", strict_error=True)

    if module_names:
        for inv_id, owner in invariant_owners:
            if owner not in module_names:
                report.warn(f"Invariant '{inv_id}' owner '{owner}' is not a declared boundary/module", strict_error=True)

    implementation_symbols = validate_implementation(implementation_doc, root, module_names, report)
    hotspot_count, work_unit_count = validate_work_units(
        work_units_doc,
        root,
        module_names,
        contract_names,
        invariant_ids,
        implementation_symbols,
        report,
    )

    for path in iter_yaml(root / "scenarios"):
        scenario = load_yaml(path, report)
        require_keys(scenario, ["name", "given", "when", "then", "must_hold"], str(path.relative_to(root)), report)
        if not isinstance(scenario, dict):
            continue
        refs = scenario.get("must_hold", [])
        if not isinstance(refs, list):
            report.error(f"{path.name}: must_hold must be a list")
            continue
        for inv_id in refs:
            if isinstance(inv_id, str) and inv_id not in invariant_ids:
                report.warn(f"{path.name}: references unknown invariant '{inv_id}'", strict_error=True)

    if not (root / "glossary.yaml").exists():
        report.warn("glossary.yaml is absent; acceptable unless terminology drift is a real risk")
    if not (root / "evolution.yaml").exists():
        report.warn("evolution.yaml is absent; acceptable unless concrete future change pressure is being tracked")

    for warning in report.warnings:
        print(f"WARNING: {warning}")
    for error in report.errors:
        print(f"ERROR: {error}")

    if report.errors:
        print(f"FAIL: {len(report.errors)} error(s), {len(report.warnings)} warning(s)")
        return 1

    print(
        "PASS: architecture state is structurally valid "
        f"({len(module_names)} boundaries/modules, {len(contract_names)} contracts, "
        f"{len(invariant_ids)} invariants, {len(implementation_symbols)} mapped symbols, "
        f"{work_unit_count} work units, {hotspot_count} shared hotspots, {len(report.warnings)} warning(s))"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
