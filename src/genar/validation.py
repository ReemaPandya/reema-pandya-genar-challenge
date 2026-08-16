from __future__ import annotations

import re
from typing import Any

MARKER_RE = re.compile(r"\[\[E:([A-Za-z0-9_.-]+)\]\]")
NUMBER_RE = re.compile(r"(?<![A-Za-z])\d[\d,]*(?:\.\d+)?")


def validate_analysis(a: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    cv = a["case_volume"]
    if cv["serious_cases"] + cv["non_serious_cases"] != cv["total_cases"]:
        errors.append("serious + non-serious does not equal total")
    if sum(a["demographics"]["sex"].values()) != cv["total_cases"]:
        errors.append("sex distribution does not sum to total")
    if sum(a["demographics"]["age_bands"].values()) != cv["total_cases"]:
        errors.append("age bands do not sum to total")
    if sum(a["trends"]["monthly_cases"].values()) != cv["total_cases"]:
        errors.append("monthly case counts do not sum to total")
    if a["expedite"]["fulfil_expedite_yes"] + a["expedite"]["fulfil_expedite_no"] != cv["total_cases"]:
        errors.append("expedite counts do not sum to total")
    return errors


def validate_markers(text: str, packet: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    markers = MARKER_RE.findall(text)
    for marker in markers:
        if marker not in packet:
            errors.append(f"unknown evidence marker: {marker}")
    factual_lines = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith(("#", "|", "-"))]
    for line in factual_lines:
        if NUMBER_RE.search(line) and not MARKER_RE.search(line):
            errors.append(f"numeric prose without evidence marker: {line[:120]}")
    return errors


def _collect_numbers(value: Any, out: set[str]) -> None:
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, (int, float)):
        out.add(str(value))
        return
    if isinstance(value, str):
        out.update(n.replace(",", "") for n in NUMBER_RE.findall(value))
        return
    if isinstance(value, dict):
        for v in value.values():
            _collect_numbers(v, out)
        return
    if isinstance(value, (list, tuple, set)):
        for v in value:
            _collect_numbers(v, out)


def allowed_numbers(packet: dict[str, Any]) -> set[str]:
    out: set[str] = {"15"}  # term in the section title/instruction
    for entry in packet.values():
        _collect_numbers(entry.get("value"), out)
    return out


def validate_numeric_grounding(text: str, packet: dict[str, Any]) -> list[str]:
    clean = MARKER_RE.sub("", text)
    allowed = allowed_numbers(packet)
    errors = []
    for num in NUMBER_RE.findall(clean):
        normalized = num.replace(",", "")
        if normalized not in allowed:
            errors.append(f"number {num} does not occur in the section evidence values")
    return sorted(set(errors))


def validate_prohibited_claims(text: str, section: str) -> list[str]:
    lower = text.lower()
    patterns = {
        "no safety concerns": "unsupported global safety conclusion",
        "confirmed safety signal": "unsupported signal conclusion",
        "caused by bisoprolol": "unsupported causal conclusion",
        "bisoprolol caused": "unsupported causal conclusion",
        "no actions occurred": "absence of supplied action data is not proof that no actions occurred",
    }
    errors = []
    for phrase, reason in patterns.items():
        if phrase in lower:
            errors.append(f"prohibited phrase {phrase!r}: {reason}")
    return errors
