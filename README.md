# GenAR AI Engineering Challenge - Grounded Safety Reporting Prototype

**Candidate:** Reema Pandya  
**Primary AI provider:** Google Gemini Developer API  
**Default model:** `gemini-3.5-flash`

This submission implements a controlled reporting system for the supplied Bisoprolol safety dataset. The core design decision is deliberately simple: **Python establishes the facts; Gemini writes only from approved facts.** The raw workbook is never handed to the model and Gemini is never trusted to do authoritative counting or arithmetic.

## What is included

- Working Python Version 0
- CSV/XLSX ingestion boundary
- Latest-case-version de-duplication
- Required deterministic analyses
- Section-specific evidence/context assembly
- Gemini Developer API drafting adapter using the `google-genai` SDK
- Credential-free deterministic fallback for tests/reproducibility
- Evidence-marker validation
- Numeric-grounding validation
- Prohibited-claim validation
- Human approve/flag gate
- Generated PADER-style Markdown report
- De-duplicated case listing
- Evidence/provenance artifacts
- Mermaid architecture diagram
- Version 1 design document
- Unit tests for critical failure modes

## Quick start

Python 3.11+ is recommended.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

The challenge dataset is intentionally **not included** in this zip. Point `--data` at the evaluator-provided workbook/CSV.

## Primary Gemini run

Create a Gemini API key and expose it through the standard environment variable. Do not put the key in source control.

PowerShell:

```powershell
$env:GEMINI_API_KEY="YOUR_KEY"
python run.py --data .\Bisoprolol_icsr_sample_1068rows.xlsx --provider gemini --model gemini-3.5-flash --review interactive --publish
```

macOS/Linux:

```bash
export GEMINI_API_KEY="YOUR_KEY"
python run.py --data ./Bisoprolol_icsr_sample_1068rows.xlsx --provider gemini --model gemini-3.5-flash --review interactive --publish
```

`--publish` is intentionally explicit. Only after all generated sections pass automated grounding checks **and** the human review gate does the command replace the submission-level `report_output.md`, `case_listing.csv`, and stable traceability artifacts.

### Credential-free reproducibility run

```bash
python run.py --data /path/to/Bisoprolol_icsr_sample_1068rows.xlsx --provider template --review auto
```

This writes into `artifacts/runtime/` and is useful for evaluator verification without an API key. The template provider is deterministic and is **not represented as AI**.

## Important note about the checked-in report

The checked-in `report_output.md` is a deterministic grounded baseline so the repository remains inspectable and testable without credentials. It was produced from the same saved evidence packets and passed the same validators.

For the final hiring submission, run the Gemini command above once with `--publish`. The published provenance will then record `gemini-developer-api`, the selected Gemini model, the dataset hash, and the human review mode. This avoids falsely claiming that an API call occurred when no Gemini credential was available during packaging.

## Architecture

See [`architecture.md`](architecture.md).

```text
Safety file
   |
   v
Ingestion / schema handling
   |
   v
Latest case-version resolver
   |
   v
Deterministic Python analyses ------------------> Case listing
   |
   v
Evidence catalog (value + provenance)
   |
   v
Section dependency map
   |
   v
Minimal section packet + section rule
   |
   v
Gemini drafting adapter
   |
   v
Grounding validators
   |
   v
Human approve / flag gate
   |
   v
Final report + provenance
```

## Why Gemini is used here

Gemini is useful for **controlled synthesis**, not for authoritative analysis. Each model call receives only the facts needed for one section. It can choose concise phrasing, connect related observations, and maintain neutral regulatory tone.

It is not asked to calculate totals, rank reactions, infer causal relationships, decide whether something is a safety signal, establish expectedness/listedness, or determine regulatory submission status.

The implementation uses Google's `google-genai` Python SDK. `genai.Client()` reads `GEMINI_API_KEY` from the environment, and the default model is configurable through `--model`.

## Deterministic code owns

- unique case counts;
- selecting the highest `safetyreportversion` per `safetyreportid`;
- serious vs. non-serious counts;
- age-band counts and percentages;
- sex and geography distributions;
- reaction parsing and distinct-case reaction frequencies;
- serious-case reaction frequencies;
- reaction outcomes;
- seriousness-criterion counts;
- expedite-criteria counts;
- monthly trends;
- rankings and percentages;
- case listing;
- reconciliation/invariant checks.

These are exact operations. Moving them into an LLM would reduce reproducibility and trust.

## Gemini owns

- concise narrative drafting from approved metrics;
- neutral regulatory wording;
- selecting which supplied observations to emphasize within a section;
- connecting supported observations without introducing new facts.

## Data handling and de-duplication

The supplied workbook contains **1,068 physical rows and 1,024 unique `safetyreportid` values**. Follow-up versions are represented as additional rows. For case-level analyses, the pipeline keeps the row with the highest `safetyreportversion` for each case ID before computing counts. This removes 44 superseded rows from case-level counting.

The challenge itself frames case counts in terms of unique case IDs, so this is treated as a deterministic preprocessing rule rather than a model decision.

A second edge case exists in the flattened MedDRA reaction field: commas separate reactions, but valid Preferred Terms may themselves contain commas, such as `Hallucination, visual`. The parser uses the parallel MedDRA-version array length to repair those flattened values rather than blindly treating every comma as a new reaction.

## Prompt and context design

The stable system instruction is in [`prompts/system.txt`](prompts/system.txt). Section-specific instructions are in [`prompts/section_rules.json`](prompts/section_rules.json).

A Gemini request is assembled conceptually as:

```text
SYSTEM
  You are a controlled drafting component.
  Use only supplied EVIDENCE.
  Do not calculate new values.
  Do not infer causality, signal status, expectedness, or absence of concerns.
  Attach evidence markers to factual claims.

USER
  SECTION: trends

  SECTION-SPECIFIC INSTRUCTION:
  Describe supported temporal observations. Avoid calling any pattern a signal.

  EVIDENCE JSON:
    trend.monthly_cases: { value: ..., provenance: ... }
    trend.peak_month: { value: ..., provenance: ... }
    trend.lowest_full_month: { value: ..., provenance: ... }
    trend.reaction_peaks: { value: ..., provenance: ... }
    trend.boundary_note: { value: ..., provenance: ... }

  Draft only this section. Do not use outside knowledge.
```

This is intentionally much smaller than sending the raw spreadsheet, the entire report, or a large retrieval dump on every request.

`src/genar/evidence.py` is the explicit dependency map controlling exactly what each report section is allowed to see.

## Grounding and traceability

Narrative claims use evidence markers such as:

```text
1,023 cases were classified as serious. [[E:case.serious]]
```

Each key resolves to `artifacts/evidence_catalog.json`, which records both the approved value and how it was produced.

Before a section reaches human review, three automated controls run:

1. **Marker validation** - rejects references to evidence keys outside the section packet.
2. **Numeric grounding** - rejects numeric values that do not occur in the allowed evidence packet.
3. **Prohibited-claim validation** - blocks unsupported phrases such as "no safety concerns were identified" or causal conclusions.

The model's prose is therefore downstream of deterministic evidence and upstream of validation and human control.

## Human control

The intended flow is:

```bash
--review interactive
```

Each generated section is displayed and must be approved or flagged. If any section is flagged, the pipeline records the decision but refuses to emit/publish a final report.

`--review auto` exists only for automated tests and credential-free demonstration. It is not intended to represent a regulated production approval workflow.

## Dataset-supported observations in the supplied challenge data

The deterministic analysis currently produces, among other things:

- 1,024 unique cases from 1,068 source rows;
- 1,023 serious cases and 1 non-serious case;
- Acute kidney injury as the most frequent distinct-case reaction;
- a July 2025 peak in monthly case volume;
- a large concentration of cases among patients aged 65 years and older;
- mixed granularity in `occurcountry`, including both country labels and the aggregate category `eu`.

These are descriptive observations only. The report does not convert them into medical or benefit-risk conclusions.

## Serious cases / 15-day Alert handling

The source includes `fulfillexpeditecriteria`, but it does not provide all information needed to verify a regulatory 15-day Alert submission, such as explicit expectedness/listedness and a specific 15-day submission date.

The pipeline therefore reports the expedite flag as an observed field and explicitly preserves that limitation rather than treating every flagged case as a verified 15-day Alert submission.

## History of actions

No structured safety-action source was supplied with the challenge inputs. The generated section says that action information was not supplied. It does **not** infer that no actions occurred.

## Evaluation at scale

For 1,000 generated reports, I would evaluate the system at several layers:

1. **Deterministic reconciliation** - all totals, distributions, date windows, and de-duplication rules must reconcile.
2. **Claim grounding** - every evidence marker resolves and every quantitative value exists in the approved section packet.
3. **Schema/missingness checks** - required source fields and expected data quality boundaries are monitored.
4. **Golden datasets** - curated edge-case datasets with expected metrics and prohibited claims.
5. **Mutation tests** - change one source fact and verify only dependent analyses/sections change.
6. **Model/prompt regression** - compare candidate Gemini/prompt versions on identical frozen evidence packets.
7. **Human quality review** - stratified domain review for factuality, omission, tone, over-interpretation, and usefulness.
8. **Operational metrics** - section rejection rate, validation failure rate, reviewer edit distance, latency, token use, and repeated failure patterns.

## Known limitations

- This is an engineering prototype, not a validated pharmacovigilance system.
- It analyzes only the supplied flat ICSR-style source.
- No exposure denominator is supplied, so it cannot estimate incidence or risk.
- No MedDRA hierarchy/SOC dictionary is supplied, so SOC mappings are not invented.
- No label/expectedness source is integrated.
- No verified 15-day submission timestamp is supplied.
- No prior reporting period is supplied, so trend analysis is descriptive within the current interval rather than a true previous-period comparison.
- `occurcountry` contains mixed geographic granularity.
- Reaction-array repair is tailored to the observed flattened structure; production should ingest structured E2B/JSON rather than reverse-engineer flattened arrays.
- The evidence-marker validator checks quantitative support and key membership, but a production evaluator should also use stronger semantic entailment checks and domain review.
- Gemini calls require user-provided credentials and network access; credentials are intentionally excluded.

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests focus on high-risk logic rather than UI/boilerplate, including latest-version selection, flattened MedDRA reaction parsing, evidence-marker validation, and unsupported safety conclusions.

## Important files

```text
src/genar/analysis.py          deterministic analyses
src/genar/loader.py            ingestion + case-version resolution
src/genar/evidence.py          evidence catalog + section dependencies
src/genar/generator.py         Gemini adapter + deterministic fallback
src/genar/validation.py        grounding checks
src/genar/review.py            human review gate
src/genar/report.py            report composition
prompts/system.txt             stable Gemini grounding contract
prompts/section_rules.json     section-specific instructions
config/pader.json              report metadata/config
artifacts/                     saved evidence/traceability baseline
architecture.md                Version 0 component/data-flow diagram
version1/design.md             future reusable report platform design
```

## Version 1

See [`version1/design.md`](version1/design.md).

The main evolution is to turn report definitions into configuration: sections declare analyses and sources, a dependency resolver materializes evidence, prompts and Gemini model settings are versioned, section regeneration is isolated, and claims become evidence-graph nodes that can be inspected by reviewers.

This keeps the current model provider replaceable. Gemini is the Version 0 provider, but the evidence and review architecture does not depend on one model vendor.

## Submission/data-use note

The evaluator-provided dataset and reference PDFs are **not included** in the submission zip, following the supplied submission guide and data-use notice. The project only includes code and generated challenge artifacts needed for evaluation.

## Pre-submission checklist for Reema Pandya

1. Install dependencies.
2. Set `GEMINI_API_KEY`.
3. Run the Gemini command with `--review interactive --publish`.
4. Approve only sections you have actually reviewed.
5. Run the unit tests.
6. Confirm `artifacts/provenance.json` says `candidate_name: Reema Pandya`, provider `gemini-developer-api`, and the Gemini model you used.
7. Confirm the zip does not contain the source dataset, `.env`, `.venv`, `__pycache__`, or API keys.
