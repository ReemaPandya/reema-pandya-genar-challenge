from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from dataclasses import asdict
from pathlib import Path

from .analysis import analyze
from .evidence import SECTION_EVIDENCE, build_catalog, section_packet
from .generator import GeminiSectionGenerator, TemplateGenerator
from .loader import deduplicate_latest, load_rows, parse_reactions, parse_yyyymmdd
from .prompts import load_prompt_assets
from .report import compose_report
from .review import all_approved, review_sections
from .validation import validate_analysis, validate_markers, validate_numeric_grounding, validate_prohibited_claims

CANDIDATE_NAME = "Reema Pandya"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_case_listing(path: Path, cases: list[dict]) -> None:
    fields = ["safetyreportid", "safetyreportversion", "receivedate", "occurcountry", "serious", "reactions", "outcomes"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for c in cases:
            d = parse_yyyymmdd(c.get("receivedate"))
            w.writerow({
                "safetyreportid": c.get("safetyreportid"),
                "safetyreportversion": c.get("safetyreportversion"),
                "receivedate": d.isoformat() if d else "",
                "occurcountry": c.get("occurcountry") or "Unknown",
                "serious": c.get("serious") or "Unknown",
                "reactions": " | ".join(parse_reactions(c)),
                "outcomes": c.get("patient_reaction_reactionoutcome") or "",
            })


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generate a grounded PADER-style report from the GenAR challenge dataset")
    p.add_argument("--data", required=True, help="Path to supplied .xlsx or .csv")
    p.add_argument("--provider", choices=["gemini", "template"], default="gemini")
    p.add_argument("--model", default="gemini-3.5-flash", help="Gemini model used when --provider gemini")
    p.add_argument("--review", choices=["auto", "interactive"], default="interactive")
    p.add_argument("--output-dir", default="artifacts/runtime")
    p.add_argument(
        "--publish",
        action="store_true",
        help="After approval, copy final report/case listing and traceability artifacts into the submission root",
    )
    return p


def _publish(root: Path, out: Path) -> None:
    shutil.copy2(out / "report_output.md", root / "report_output.md")
    shutil.copy2(out / "case_listing.csv", root / "case_listing.csv")
    stable_artifacts = root / "artifacts"
    stable_artifacts.mkdir(exist_ok=True)
    for name in [
        "analysis.json",
        "evidence_catalog.json",
        "section_packets.json",
        "generated_sections.json",
        "generation_attempts.json",
        "review_decisions.json",
        "validation.json",
        "provenance.json",
    ]:
        shutil.copy2(out / name, stable_artifacts / name)


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    data_path = Path(args.data).resolve()
    out = (root / args.output_dir).resolve() if not Path(args.output_dir).is_absolute() else Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    config = json.loads((root / "config" / "pader.json").read_text(encoding="utf-8"))
    system_prompt, section_rules = load_prompt_assets(root)

    rows = load_rows(data_path)
    cases, audit = deduplicate_latest(rows)
    analysis = analyze(cases, audit, top_n=config.get("top_reactions", 15))
    analysis_errors = validate_analysis(analysis)
    if analysis_errors:
        raise RuntimeError("Analysis validation failed: " + "; ".join(analysis_errors))

    catalog = build_catalog(analysis)
    packets = {name: section_packet(name, catalog) for name in SECTION_EVIDENCE}

    if args.provider == "gemini":
        generator = GeminiSectionGenerator(model=args.model)
    else:
        generator = TemplateGenerator()

    sections: dict[str, str] = {}
    validation: dict[str, dict[str, object]] = {}
    generation_attempts: dict[str, list[dict[str, object]]] = {}
    max_attempts = 3 if args.provider == "gemini" else 1

    for section, packet in packets.items():
        correction: str | None = None
        generation_attempts[section] = []

        for attempt in range(1, max_attempts + 1):
            text = generator.generate(
                section,
                packet,
                system_prompt,
                section_rules[section],
                correction=correction,
            )
            marker_errors = validate_markers(text, packet)
            numeric_errors = validate_numeric_grounding(text, packet)
            prohibited_errors = validate_prohibited_claims(text, section)
            current_validation = {
                "marker_errors": marker_errors,
                "numeric_errors": numeric_errors,
                "prohibited_claim_errors": prohibited_errors,
            }
            generation_attempts[section].append({
                "attempt": attempt,
                "draft": text,
                "validation": current_validation,
            })

            if not (marker_errors or numeric_errors or prohibited_errors):
                validation[section] = {
                    **current_validation,
                    "attempts_used": attempt,
                }
                sections[section] = text
                break

            correction = json.dumps(current_validation, ensure_ascii=False)
            print(
                f"Validation rejected {section} attempt {attempt}/{max_attempts}; "
                "retrying with validator feedback..."
            )
        else:
            print(
                f"Gemini could not produce a grounded {section} section "
                f"after {max_attempts} attempts. Using deterministic fallback."
            )

            fallback = TemplateGenerator()

            text = fallback.generate(
                section,
                packet,
                system_prompt,
                section_rules[section],
            )

            marker_errors = validate_markers(text, packet)
            numeric_errors = validate_numeric_grounding(text, packet)
            prohibited_errors = validate_prohibited_claims(text, section)

            fallback_validation = {
                "marker_errors": marker_errors,
                "numeric_errors": numeric_errors,
                "prohibited_claim_errors": prohibited_errors,
            }

            generation_attempts[section].append({
                "attempt": "deterministic_fallback",
                "draft": text,
                "validation": fallback_validation,
            })

            if marker_errors or numeric_errors or prohibited_errors:
                (out / "generation_attempts.json").write_text(
                    json.dumps(
                        generation_attempts,
                        indent=2,
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )

                raise RuntimeError(
                    f"Deterministic fallback validation failed for {section}: "
                    f"{fallback_validation}"
                )

            sections[section] = text

            validation[section] = {
                **fallback_validation,
                "attempts_used": max_attempts,
                "fallback_used": True,
            }

            # Save draft/validation evidence before human review so a reviewer can inspect a
            # failed or flagged run without pretending it became final.
            (out / "analysis.json").write_text(json.dumps(analysis, indent=2, ensure_ascii=False), encoding="utf-8")
            (out / "evidence_catalog.json").write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
            (out / "section_packets.json").write_text(json.dumps(packets, indent=2, ensure_ascii=False), encoding="utf-8")
            (out / "generated_sections.json").write_text(json.dumps(sections, indent=2, ensure_ascii=False), encoding="utf-8")
            (out / "generation_attempts.json").write_text(json.dumps(generation_attempts, indent=2, ensure_ascii=False), encoding="utf-8")
            (out / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")

            decisions = review_sections(sections, args.review)
            (out / "review_decisions.json").write_text(json.dumps([asdict(d) for d in decisions], indent=2), encoding="utf-8")
            if not all_approved(decisions):
                raise RuntimeError("One or more sections were flagged during human review; final report was not emitted")

            report = compose_report(config, analysis, sections)
            (out / "report_output.md").write_text(report, encoding="utf-8")
            _write_case_listing(out / "case_listing.csv", cases)
            provenance = {
                "candidate_name": CANDIDATE_NAME,
                "dataset_file": data_path.name,
                "dataset_sha256": _sha256(data_path),
                "source_rows": audit["source_rows"],
                "unique_cases": audit["unique_cases"],
                "provider": generator.name,
                "model": generator.model,
                "prompt_files": ["prompts/system.txt", "prompts/section_rules.json"],
                "human_review_mode": args.review,
                "final_emitted": True,
            }
            (out / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")

            if args.publish:
                _publish(root, out)
                print(f"Published submission report to {root / 'report_output.md'}")

            print(f"Generated {out / 'report_output.md'}")
            print(f"Unique cases: {analysis['case_volume']['total_cases']} from {analysis['case_volume']['source_rows']} source rows")
            print(f"Provider: {generator.name} / {generator.model}")
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
