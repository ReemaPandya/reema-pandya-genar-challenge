from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from typing import Any

from .loader import parse_reactions, parse_yyyymmdd, split_multi


def _pct(n: int, d: int) -> float:
    return round((100.0 * n / d), 1) if d else 0.0


def _norm(value: Any, unknown: str = "Unknown") -> str:
    if value in (None, ""):
        return unknown
    text = str(value).strip()
    return text if text else unknown


def age_years(row: dict[str, Any]) -> float | None:
    raw_age = row.get("patient_patientonsetage")
    unit = _norm(row.get("patient_patientonsetageunit"), "").lower()
    try:
        age = float(raw_age)
    except (TypeError, ValueError):
        return None
    if unit == "year":
        return age
    if unit == "month":
        return age / 12.0
    if unit == "week":
        return age / 52.1429
    if unit == "day":
        return age / 365.25
    return None


def age_band(value: float | None) -> str:
    if value is None:
        return "Unknown"
    if value < 18:
        return "<18"
    if value < 45:
        return "18-44"
    if value < 65:
        return "45-64"
    if value < 75:
        return "65-74"
    return "75+"


def analyze(cases: list[dict[str, Any]], audit: dict[str, Any], top_n: int = 15) -> dict[str, Any]:
    total = len(cases)
    serious = [c for c in cases if _norm(c.get("serious"), "").lower() == "serious"]
    non_serious = total - len(serious)

    dates = [parse_yyyymmdd(c.get("receivedate")) for c in cases]
    dates = [d for d in dates if d is not None]
    reporting_start = min(dates)
    reporting_end = max(dates)

    sex = Counter(_norm(c.get("patient_patientsex")).lower() for c in cases)
    age_counts = Counter(age_band(age_years(c)) for c in cases)
    valid_ages = [age_years(c) for c in cases]
    valid_ages = [v for v in valid_ages if v is not None]

    countries = Counter(_norm(c.get("occurcountry")) for c in cases)
    report_types = Counter(_norm(c.get("reporttype")) for c in cases)

    reaction_case_counts: Counter[str] = Counter()
    serious_reaction_case_counts: Counter[str] = Counter()
    reaction_ids: dict[str, list[str]] = defaultdict(list)
    serious_reaction_ids: dict[str, list[str]] = defaultdict(list)
    reaction_event_count = 0
    serious_reaction_event_count = 0
    reaction_parse_warnings = 0

    outcomes_event: Counter[str] = Counter()
    outcomes_case: Counter[str] = Counter()

    for case in cases:
        case_id = str(case.get("safetyreportid"))
        reactions = parse_reactions(case)
        reaction_event_count += len(reactions)
        if case.get("_reaction_parse_warning"):
            reaction_parse_warnings += 1
        for reaction in set(reactions):
            reaction_case_counts[reaction] += 1
            reaction_ids[reaction].append(case_id)
        if _norm(case.get("serious"), "").lower() == "serious":
            serious_reaction_event_count += len(reactions)
            for reaction in set(reactions):
                serious_reaction_case_counts[reaction] += 1
                serious_reaction_ids[reaction].append(case_id)

        outcomes = split_multi(case.get("patient_reaction_reactionoutcome"))
        outcomes_event.update(_norm(v).lower() for v in outcomes)
        outcomes_case.update(set(_norm(v).lower() for v in outcomes))

    monthly_cases: Counter[str] = Counter()
    monthly_serious: Counter[str] = Counter()
    monthly_reactions: dict[str, Counter[str]] = defaultdict(Counter)
    for case in cases:
        received = parse_yyyymmdd(case.get("receivedate"))
        if not received:
            continue
        month = received.strftime("%Y-%m")
        monthly_cases[month] += 1
        if _norm(case.get("serious"), "").lower() == "serious":
            monthly_serious[month] += 1
        for reaction in set(parse_reactions(case)):
            monthly_reactions[reaction][month] += 1

    expedite = [c for c in cases if _norm(c.get("fulfillexpeditecriteria"), "").lower() == "yes"]
    expedite_types = Counter(_norm(c.get("reporttype")) for c in expedite)

    seriousness_criteria = {}
    for field, label in [
        ("seriousnessdeath", "death"),
        ("seriousnesslifethreatening", "life_threatening"),
        ("seriousnesshospitalization", "hospitalization"),
        ("seriousnessdisabling", "disabling"),
        ("seriousnesscongenitalanomali", "congenital_anomaly"),
        ("seriousnessother", "other_medically_important"),
    ]:
        count = sum(1 for c in cases if _norm(c.get(field), "").lower() == "yes")
        seriousness_criteria[label] = count

    top_reactions = [
        {
            "reaction": term,
            "cases": count,
            "pct_cases": _pct(count, total),
            "case_ids": sorted(reaction_ids[term]),
        }
        for term, count in reaction_case_counts.most_common(top_n)
    ]
    top_serious_reactions = [
        {
            "reaction": term,
            "serious_cases": count,
            "pct_serious_cases": _pct(count, len(serious)),
            "case_ids": sorted(serious_reaction_ids[term]),
        }
        for term, count in serious_reaction_case_counts.most_common(top_n)
    ]

    # Trend observations are deterministic selections, not LLM-discovered arithmetic.
    monthly_sorted = dict(sorted(monthly_cases.items()))
    peak_month, peak_count = max(monthly_cases.items(), key=lambda kv: (kv[1], kv[0]))
    full_months = {m: c for m, c in monthly_cases.items() if m not in {reporting_start.strftime('%Y-%m'), reporting_end.strftime('%Y-%m')}}
    lowest_full_month, lowest_full_count = min(full_months.items(), key=lambda kv: (kv[1], kv[0])) if full_months else (None, None)

    reaction_peaks = []
    for item in top_reactions[:5]:
        term = item["reaction"]
        counts = monthly_reactions.get(term, {})
        if counts:
            peak = max(counts.values())
            months = sorted([m for m, c in counts.items() if c == peak])
            reaction_peaks.append({"reaction": term, "peak_cases": peak, "peak_months": months})

    older_65 = age_counts["65-74"] + age_counts["75+"]
    known_age = total - age_counts["Unknown"]

    data_quality = {
        **audit,
        "cases_missing_or_unusable_age": age_counts["Unknown"],
        "cases_unknown_sex": sex.get("unknown", 0),
        "cases_unknown_country": countries.get("Unknown", 0),
        "reaction_parse_warnings_after_alignment": reaction_parse_warnings,
        "mixed_geography_granularity": "occurcountry includes both country values and the aggregate value 'eu'",
    }

    return {
        "reporting_period": {"start": reporting_start.isoformat(), "end": reporting_end.isoformat()},
        "case_volume": {
            "total_cases": total,
            "serious_cases": len(serious),
            "non_serious_cases": non_serious,
            "serious_pct": _pct(len(serious), total),
            "source_rows": audit["source_rows"],
            "followup_rows_removed": audit["followup_rows_removed"],
        },
        "demographics": {
            "sex": dict(sex),
            "age_bands": {k: age_counts.get(k, 0) for k in ["<18", "18-44", "45-64", "65-74", "75+", "Unknown"]},
            "known_age_cases": known_age,
            "age_65_plus_cases": older_65,
            "age_65_plus_pct_all": _pct(older_65, total),
            "age_65_plus_pct_known_age": _pct(older_65, known_age),
        },
        "geography": {
            "counts": dict(countries.most_common()),
            "top": [{"location": k, "cases": v, "pct_cases": _pct(v, total)} for k, v in countries.most_common(12)],
        },
        "report_sources": dict(report_types),
        "reactions": {
            "distinct_terms": len(reaction_case_counts),
            "reaction_events_after_case_dedup": reaction_event_count,
            "serious_reaction_events_after_case_dedup": serious_reaction_event_count,
            "top": top_reactions,
            "top_serious": top_serious_reactions,
        },
        "outcomes": {
            "reaction_event_counts": dict(outcomes_event.most_common()),
            "case_has_outcome_counts": dict(outcomes_case.most_common()),
            "note": "A case may contribute to multiple outcome categories when it contains multiple reactions.",
        },
        "expedite": {
            "fulfil_expedite_yes": len(expedite),
            "fulfil_expedite_no": total - len(expedite),
            "yes_pct": _pct(len(expedite), total),
            "source_types": dict(expedite_types),
            "limitations": [
                "No explicit expectedness/listedness field is supplied.",
                "No explicit 15-day submission date is supplied.",
                "fulfillexpeditecriteria is treated as an expedite-criteria flag, not proof of a verified 15-day Alert submission."
            ],
        },
        "seriousness_criteria": seriousness_criteria,
        "trends": {
            "monthly_cases": monthly_sorted,
            "monthly_serious": dict(sorted(monthly_serious.items())),
            "peak_month": peak_month,
            "peak_month_cases": peak_count,
            "lowest_full_month": lowest_full_month,
            "lowest_full_month_cases": lowest_full_count,
            "top_reaction_monthly_peaks": reaction_peaks,
            "boundary_note": f"{reporting_start.strftime('%Y-%m')} and {reporting_end.strftime('%Y-%m')} are partial calendar months because the reporting period runs {reporting_start.isoformat()} through {reporting_end.isoformat()}.",
        },
        "history_actions": {
            "supplied": False,
            "statement": "No structured safety-action history or supporting action document was supplied with the challenge dataset. This does not establish that no actions occurred."
        },
        "data_quality": data_quality,
    }
