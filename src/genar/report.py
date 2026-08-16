from __future__ import annotations

from typing import Any


SECTION_TITLES = {
    "narrative_summary": "Narrative Summary and Analysis",
    "summary_cases": "Summary Analysis of Cases",
    "reaction_analysis": "Reaction / Adverse Event Analysis",
    "serious_alerts": "Serious Cases / 15-Day Alert Assessment",
    "trends": "Trends and Important Observations",
    "history_actions": "History of Actions",
}


def _table(rows: list[list[Any]], headers: list[str]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    lines += ["| " + " | ".join(str(x) for x in row) + " |" for row in rows]
    return "\n".join(lines)


def compose_report(config: dict[str, Any], analysis: dict[str, Any], sections: dict[str, str]) -> str:
    period = analysis["reporting_period"]
    chunks = [
        "# Periodic Adverse Drug Experience Report (PADER-style)",
        "",
        f"**Product:** {config['product']}  ",
        f"**Application identifier:** {config.get('application_identifier', 'Not supplied')}  ",
        f"**Report type:** {config['report_type']}  ",
        f"**Reporting period / data cut-off:** {period['start']} to {period['end']}  ",
        "",
        "> This is a simplified engineering-challenge output. It is not a regulatory submission and does not make medical or benefit-risk conclusions beyond the supplied evidence.",
        "",
    ]
    for key in ["narrative_summary", "summary_cases", "reaction_analysis", "serious_alerts", "trends", "history_actions"]:
        chunks += [f"## {SECTION_TITLES[key]}", "", sections[key], ""]

    # Deterministic tables are rendered directly from approved analysis results.
    chunks += ["## Deterministic Supporting Tables", "", "### Monthly case volume", ""]
    chunks.append(_table([[m, c] for m, c in analysis["trends"]["monthly_cases"].items()], ["Received month", "Unique cases"]))
    chunks += ["", "### Top reactions (distinct cases)", ""]
    chunks.append(_table([[x["reaction"], x["cases"], f"{x['pct_cases']}%"] for x in analysis["reactions"]["top"]], ["Reaction / MedDRA PT", "Cases", "% of cases"]))
    chunks += ["", "### Age distribution", ""]
    chunks.append(_table([[k, v] for k, v in analysis["demographics"]["age_bands"].items()], ["Age band", "Cases"]))
    chunks += ["", "### Sex distribution", ""]
    chunks.append(_table([[k, v] for k, v in analysis["demographics"]["sex"].items()], ["Sex", "Cases"]))
    chunks += ["", "### Leading geography categories", ""]
    chunks.append(_table([[x["location"], x["cases"], f"{x['pct_cases']}%"] for x in analysis["geography"]["top"]], ["occurcountry category", "Cases", "% of cases"]))

    chunks += [
        "",
        "## Case Index / Listing",
        "",
        f"A structured listing of all {analysis['case_volume']['total_cases']:,} de-duplicated cases is provided in `case_listing.csv`. It contains case ID, latest version, reactions, seriousness, received date, occurcountry, and reported reaction outcomes.",
        "",
        "## Traceability",
        "",
        "Generated narrative claims use `[[E:...]]` markers. The corresponding values and provenance are stored in `artifacts/evidence_catalog.json`. Section-scoped packets are stored in `artifacts/section_packets.json`.",
        "",
        "## Data Limitations",
        "",
        "- The source is a flattened safety dataset; follow-up versions were de-duplicated by selecting the highest `safetyreportversion` for each `safetyreportid`.",
        "- `occurcountry` mixes country labels with the aggregate value `eu`; geography is therefore reported as source categories rather than normalized countries.",
        "- Age is missing or unusable for some cases; percentages are labeled according to the denominator used.",
        "- The dataset does not provide explicit expectedness/listedness or 15-day submission dates. `fulfillexpeditecriteria` is therefore not treated as proof of a verified 15-day Alert submission.",
        "- No safety-action history source was supplied; absence of supplied action data does not mean no actions occurred.",
        "- Counts are report counts, not incidence rates; exposure denominators are not supplied.",
    ]
    return "\n".join(chunks).strip() + "\n"
