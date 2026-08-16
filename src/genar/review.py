from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReviewDecision:
    section: str
    status: str
    note: str = ""


def review_sections(sections: dict[str, str], mode: str) -> list[ReviewDecision]:
    if mode == "auto":
        return [ReviewDecision(section=k, status="auto-accepted-for-demo") for k in sections]
    if mode != "interactive":
        raise ValueError(f"Unsupported review mode: {mode}")

    decisions: list[ReviewDecision] = []
    for name, text in sections.items():
        print("\n" + "=" * 80)
        print(f"SECTION: {name}\n")
        print(text)
        print("=" * 80)
        choice = input("Approve [a] or flag [f]? ").strip().lower()
        if choice == "a":
            decisions.append(ReviewDecision(name, "approved"))
        else:
            note = input("Flag note: ").strip()
            decisions.append(ReviewDecision(name, "flagged", note))
    return decisions


def all_approved(decisions: list[ReviewDecision]) -> bool:
    return all(d.status in {"approved", "auto-accepted-for-demo"} for d in decisions)
