from __future__ import annotations

from typing import Any


def _entry(value: Any, provenance: str, interpretation: str | None = None) -> dict[str, Any]:
    out = {"value": value, "provenance": provenance}
    if interpretation:
        out["interpretation_constraint"] = interpretation
    return out


def build_catalog(a: dict[str, Any]) -> dict[str, dict[str, Any]]:
    c: dict[str, dict[str, Any]] = {}
    c["period.start"] = _entry(a["reporting_period"]["start"], "minimum receivedate among latest case versions")
    c["period.end"] = _entry(a["reporting_period"]["end"], "maximum receivedate among latest case versions")
    c["case.total"] = _entry(a["case_volume"]["total_cases"], "count distinct safetyreportid after selecting highest safetyreportversion")
    c["case.serious"] = _entry(a["case_volume"]["serious_cases"], "latest case versions where serious == 'serious'")
    c["case.non_serious"] = _entry(a["case_volume"]["non_serious_cases"], "distinct cases minus serious cases")
    c["case.serious_pct"] = _entry(a["case_volume"]["serious_pct"], "100 * serious_cases / total_cases")
    c["source.rows"] = _entry(a["case_volume"]["source_rows"], "physical rows loaded from source workbook")
    c["source.followups_removed"] = _entry(a["case_volume"]["followup_rows_removed"], "source rows minus distinct latest case versions")

    for key, value in a["demographics"]["sex"].items():
        c[f"sex.{key}"] = _entry(value, f"latest cases grouped by patient_patientsex == {key!r}")
    for key, value in a["demographics"]["age_bands"].items():
        safe = key.replace("<", "lt").replace("+", "plus").replace("-", "_").lower()
        c[f"age.{safe}"] = _entry(value, f"latest cases assigned to derived age band {key}")
    c["age.65plus"] = _entry(a["demographics"]["age_65_plus_cases"], "sum of 65-74 and 75+ age bands")
    c["age.65plus_pct_all"] = _entry(a["demographics"]["age_65_plus_pct_all"], "age_65_plus_cases / all distinct cases")
    c["age.65plus_pct_known"] = _entry(a["demographics"]["age_65_plus_pct_known_age"], "age_65_plus_cases / cases with usable age")
    c["age.band_definitions"] = _entry(["<18", "18-44", "45-64", "65-74", "75+"], "configured deterministic age-band boundaries")

    for i, item in enumerate(a["geography"]["top"], start=1):
        c[f"geo.top{i}"] = _entry({"location": item["location"], "cases": item["cases"], "pct_cases": item["pct_cases"]}, "latest cases grouped by occurcountry")
    c["geo.mixed_granularity"] = _entry(a["data_quality"]["mixed_geography_granularity"], "observed category values in occurcountry")

    for i, item in enumerate(a["reactions"]["top"], start=1):
        c[f"reaction.top{i}"] = _entry({k: item[k] for k in ("reaction", "cases", "pct_cases")}, "distinct latest cases containing MedDRA PT after aligned reaction parsing")
    for i, item in enumerate(a["reactions"]["top_serious"], start=1):
        c[f"reaction.serious_top{i}"] = _entry({k: item[k] for k in ("reaction", "serious_cases", "pct_serious_cases")}, "serious latest cases containing MedDRA PT")

    for key, value in a["outcomes"]["reaction_event_counts"].items():
        safe = key.replace("/", "_").replace(" ", "_").replace("-", "_")
        c[f"outcome.event.{safe}"] = _entry(value, f"count of reaction-level outcome value {key!r} among latest case versions")
    for key, value in a["outcomes"]["case_has_outcome_counts"].items():
        safe = key.replace("/", "_").replace(" ", "_").replace("-", "_")
        c[f"outcome.case.{safe}"] = _entry(value, f"distinct latest cases containing at least one reaction outcome {key!r}")
    c["outcome.multilabel_note"] = _entry(a["outcomes"]["note"], "outcome field structure")

    c["expedite.yes"] = _entry(a["expedite"]["fulfil_expedite_yes"], "latest cases where fulfillexpeditecriteria == 'yes'", "Do not equate automatically with verified 15-day Alert submission")
    c["expedite.no"] = _entry(a["expedite"]["fulfil_expedite_no"], "latest cases where fulfillexpeditecriteria != 'yes'")
    c["expedite.pct"] = _entry(a["expedite"]["yes_pct"], "expedite yes / all distinct cases")
    c["expedite.limitations"] = _entry(a["expedite"]["limitations"], "field-availability audit")
    for key, value in a["seriousness_criteria"].items():
        c[f"seriousness.{key}"] = _entry(value, f"latest cases where corresponding seriousness flag for {key} == 'yes'")

    c["trend.monthly_cases"] = _entry(a["trends"]["monthly_cases"], "distinct latest cases grouped by receivedate calendar month")
    c["trend.peak_month"] = _entry({"month": a["trends"]["peak_month"], "cases": a["trends"]["peak_month_cases"]}, "argmax of monthly distinct-case counts")
    c["trend.lowest_full_month"] = _entry({"month": a["trends"]["lowest_full_month"], "cases": a["trends"]["lowest_full_month_cases"]}, "minimum among full calendar months inside reporting interval")
    c["trend.reaction_peaks"] = _entry(a["trends"]["top_reaction_monthly_peaks"], "monthly counts for the five most common reactions")
    c["trend.boundary_note"] = _entry(a["trends"]["boundary_note"], "reporting-period boundary check")

    c["actions.supplied"] = _entry(a["history_actions"]["supplied"], "challenge input inventory")
    c["actions.statement"] = _entry(a["history_actions"]["statement"], "challenge input inventory", "Absence of supplied action information is not evidence that no action occurred")

    c["quality.audit"] = _entry(a["data_quality"], "deterministic ingestion and field-quality checks")
    return c


SECTION_EVIDENCE = {
    "narrative_summary": [
        "period.start", "period.end", "case.total", "case.serious", "case.non_serious", "case.serious_pct",
        "age.65plus", "age.65plus_pct_all", "age.65plus_pct_known", "age.band_definitions", "sex.female", "sex.male", "sex.unknown",
        "geo.top1", "geo.top2", "geo.top3", "geo.mixed_granularity",
        "reaction.top1", "reaction.top2", "reaction.top3", "reaction.top4", "reaction.top5",
        "outcome.case.recovered_resolved", "outcome.case.unknown", "outcome.case.fatal",
        "trend.peak_month", "trend.lowest_full_month", "trend.boundary_note"
    ],
    "summary_cases": [
        "case.total", "case.serious", "case.non_serious", "case.serious_pct",
        "age.lt18", "age.18_44", "age.45_64", "age.65_74", "age.75plus", "age.unknown", "age.band_definitions",
        "sex.female", "sex.male", "sex.unknown",
        "geo.top1", "geo.top2", "geo.top3", "geo.top4", "geo.top5", "geo.mixed_granularity",
        "source.rows", "source.followups_removed"
    ],
    "reaction_analysis": [
        "case.non_serious",
        *[f"reaction.top{i}" for i in range(1, 16)],
        *[f"reaction.serious_top{i}" for i in range(1, 16)],
        "outcome.multilabel_note",
        "outcome.event.recovered_resolved", "outcome.event.unknown", "outcome.event.not_recovered_not_resolved_ongoing",
        "outcome.event.recovering_resolving", "outcome.event.fatal", "outcome.event.recovered_resolved_with_sequelae"
    ],
    "serious_alerts": [
        "case.serious", "case.non_serious", "expedite.yes", "expedite.no", "expedite.pct", "expedite.limitations",
        "seriousness.death", "seriousness.life_threatening", "seriousness.hospitalization", "seriousness.disabling",
        "seriousness.congenital_anomaly", "seriousness.other_medically_important"
    ],
    "trends": [
        "trend.monthly_cases", "trend.peak_month", "trend.lowest_full_month", "trend.reaction_peaks", "trend.boundary_note",
        "age.65plus", "age.65plus_pct_all", "age.65plus_pct_known", "age.band_definitions", "geo.mixed_granularity"
    ],
    "history_actions": ["actions.supplied", "actions.statement"]
}


def section_packet(section: str, catalog: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    keys = SECTION_EVIDENCE[section]
    missing = [k for k in keys if k not in catalog]
    if missing:
        raise KeyError(f"Missing evidence keys for {section}: {missing}")
    return {k: catalog[k] for k in keys}
