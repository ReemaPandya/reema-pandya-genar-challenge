# Version 1 Design: From PADER Prototype to Configurable Safety-Report Platform

## Goal

Keep the evidence engine stable while report types (PADER, PSUR/PBRER, DSUR, CSR) become configuration. New report types should primarily add section definitions, evidence dependencies, data adapters, and drafting rules rather than new orchestration code.

## Proposed configuration model

Each report type would declare:

```yaml
report_type: pbrer
sections:
  - id: interval_case_summary
    analyses: [case_volume, seriousness, geography]
    prompt_rule: prompts/pbrer/interval_case_summary.txt
    validators: [evidence_markers, numeric_grounding]
  - id: signal_evaluation
    analyses: [signal_inputs, prior_period_comparison]
    required_sources: [icsr, signal_registry, prior_report]
```

Analyses become named, reusable functions with typed outputs. A dependency resolver runs only what the selected sections require.

## Additional components

1. **Data adapters and canonical model** - map FAERS/E2B-like flat files, structured internal ICSR data, prior reports, action logs, and label documents into versioned canonical records.
2. **Evidence graph** - every metric/claim node points to input rows/case IDs, transformation version, and section(s) that consumed it.
3. **Prompt registry** - version prompts independently from code; store prompt hash, model, parameters, and packet hash with each generated section.
4. **Section regeneration** - regenerate one section when evidence changes without rerunning unrelated sections.
5. **Prior-period comparison** - deterministic delta/ratio analyses with explicit denominator and partial-period checks.
6. **Evaluation service** - run structural, numerical, citation, omission, and prohibited-claim tests before human review.
7. **Human review workflow** - approve, edit, flag, assign, comment, and lock sections; retain audit history.

## Evidence tracing UX

A sentence such as "1,023 cases were serious" would carry a machine-readable evidence ID. Clicking it would show:

- metric definition;
- value and denominator;
- source dataset hash;
- de-duplication rule;
- contributing case IDs;
- analysis code/version;
- prompt packet and model version;
- reviewer disposition.

This makes traceability a product capability rather than a prose convention.

## Evaluation at scale

For 1,000 generated reports I would run:

- **Deterministic invariants:** totals reconcile; distributions sum correctly; date windows are respected; no duplicate case versions.
- **Claim grounding:** every evidence marker resolves; every quantitative claim is present in its approved packet; unsupported regulatory conclusions are blocked.
- **Golden-set regression:** curated reports with expected metrics and prohibited statements across edge cases.
- **Mutation tests:** deliberately alter a source value and verify only dependent analyses/sections change.
- **LLM quality sampling:** domain reviewers score factuality, omission, tone, usefulness, and over-interpretation on stratified samples.
- **Drift monitoring:** compare model/prompt versions on the same evidence packets before rollout.

## Why this survives new report types

The current Version 0 already separates ingestion, analyses, evidence, section dependencies, prompts, generation, validation, review, and rendering. PADER-specific content lives mainly in `config/`, the section dependency map, and prompt rules. Version 1 would move the remaining section-specific Python structure into declarative configuration and add source adapters needed by reports that rely on data beyond ICSRs.

## Model-provider evolution

Version 0 uses Gemini through a thin `SectionGenerator` adapter. Version 1 would keep that interface provider-neutral while storing provider/model configuration per report definition. That allows controlled Gemini model upgrades and A/B regression testing without changing deterministic analyses, evidence dependencies, or review logic.
