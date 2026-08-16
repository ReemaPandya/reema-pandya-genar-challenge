from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_prompt_assets(root: Path) -> tuple[str, dict[str, str]]:
    system = (root / "prompts" / "system.txt").read_text(encoding="utf-8")
    rules = json.loads((root / "prompts" / "section_rules.json").read_text(encoding="utf-8"))
    return system, rules


def build_context(
    section: str,
    packet: dict[str, Any],
    section_rule: str,
    correction: str | None = None,
) -> str:
    correction_block = ""
    if correction:
        correction_block = (
            "\n\nVALIDATION FEEDBACK FROM THE PREVIOUS DRAFT:\n"
            f"{correction}\n"
            "Rewrite the section from scratch and correct every issue above. Do not defend or explain the previous draft."
        )

    return (
        f"SECTION: {section}\n\n"
        f"SECTION-SPECIFIC INSTRUCTION:\n{section_rule}\n\n"
        "EVIDENCE JSON (the complete allowed factual context for this section):\n"
        f"{json.dumps(packet, indent=2, ensure_ascii=False)}\n\n"
        "NUMERIC SAFETY RULE:\n"
        "- Do not introduce or calculate any new number, percentage, duration, interval, rank, count, date, age, or quantity.\n"
        "- Every numeric token you write must already occur verbatim in an EVIDENCE value for this section (except the literal regulatory term '15-day' when the section explicitly discusses it).\n"
        "- Every sentence or paragraph containing a numeric value must include the relevant [[E:key]] evidence marker on the same line.\n"
        "- Do not repeat numeric age-band boundary labels in prose; refer to them as configured age bands and report only supported counts.\n"
        "- Do not derive a duration from start/end dates (for example, do not convert dates into a number of months or days).\n"
        "- Do not spell out a newly derived quantity in words to bypass this rule.\n"
        "- If a useful quantity is not explicitly present in EVIDENCE, omit it or state qualitatively that it is not supplied.\n\n"
        "Draft only this section. Do not use outside knowledge."
        + correction_block
    )
