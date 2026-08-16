# Periodic Adverse Drug Experience Report (PADER-style)

**Product:** Bisoprolol  
**Application identifier:** B-1  
**Report type:** PADER-style periodic safety report  
**Reporting period / data cut-off:** 2024-12-27 to 2025-12-26  

> This is a simplified engineering-challenge output. It is not a regulatory submission and does not make medical or benefit-risk conclusions beyond the supplied evidence.

## Narrative Summary and Analysis

During the reporting period, 1,024 unique cases were identified after case-version de-duplication; 1,023 (99.9%) were classified as serious and 1 as non-serious. [[E:case.total]] [[E:case.serious]] [[E:case.serious_pct]] [[E:case.non_serious]]

Patients aged 65 years or older accounted for 674 cases (65.8% of all cases; 71.9% among cases with usable age). [[E:age.65plus]] [[E:age.65plus_pct_all]] [[E:age.65plus_pct_known]] The sex distribution included 503 female, 493 male, and 28 unknown-sex cases. [[E:sex.female]] [[E:sex.male]] [[E:sex.unknown]]

The leading occurcountry categories were eu (342), united kingdom (278), and france (185). [[E:geo.top1]] [[E:geo.top2]] [[E:geo.top3]] The geography field mixes country and aggregate-region labels, so these categories should not be interpreted as a harmonized country taxonomy. [[E:geo.mixed_granularity]]

The most frequently reported reactions at distinct-case level were Acute kidney injury (80 cases), Drug ineffective (54), and Hypotension (46). [[E:reaction.top1]] [[E:reaction.top2]] [[E:reaction.top3]] Calendar-month case volume was highest in 2025-07 with 109 cases; the lowest full calendar month was 2025-08 with 64 cases. [[E:trend.peak_month]] [[E:trend.lowest_full_month]] These are descriptive observations and are not, by themselves, evidence of a safety signal.

## Summary Analysis of Cases

The source contained 1,068 rows. Selecting the highest safetyreportversion for each safetyreportid removed 44 follow-up rows from case-level counting and yielded 1,024 unique cases. [[E:source.rows]] [[E:source.followups_removed]] [[E:case.total]]

Serious cases: 1,023; non-serious cases: 1. [[E:case.serious]] [[E:case.non_serious]]

Age bands were <18: 16; 18-44: 44; 45-64: 204; 65-74: 266; 75+: 408; unknown/unusable: 86. [[E:age.lt18]] [[E:age.18_44]] [[E:age.45_64]] [[E:age.65_74]] [[E:age.75plus]] [[E:age.unknown]]

Sex was reported as female in 503 cases, male in 493, and unknown in 28. [[E:sex.female]] [[E:sex.male]] [[E:sex.unknown]]

The five largest occurcountry categories were eu (342), united kingdom (278), france (185), canada (55), italy (51). [[E:geo.top1]] [[E:geo.top2]] [[E:geo.top3]] [[E:geo.top4]] [[E:geo.top5]]

## Reaction / Adverse Event Analysis

At distinct-case level, the ten most frequently reported reactions were: Acute kidney injury (80), Drug ineffective (54), Hypotension (46), Drug interaction (43), Dyspnoea (38), Bradycardia (37), Dizziness (36), Fatigue (33), Off label use (31), Fall (30). [[E:reaction.top1]] [[E:reaction.top2]] [[E:reaction.top3]] [[E:reaction.top4]] [[E:reaction.top5]] [[E:reaction.top6]] [[E:reaction.top7]] [[E:reaction.top8]] [[E:reaction.top9]] [[E:reaction.top10]]

Among serious cases, the ten most frequently reported reactions were: Acute kidney injury (80), Drug ineffective (53), Hypotension (46), Drug interaction (43), Dyspnoea (38), Bradycardia (37), Dizziness (36), Fatigue (33), Off label use (31), Fall (30). [[E:reaction.serious_top1]] [[E:reaction.serious_top2]] [[E:reaction.serious_top3]] [[E:reaction.serious_top4]] [[E:reaction.serious_top5]] [[E:reaction.serious_top6]] [[E:reaction.serious_top7]] [[E:reaction.serious_top8]] [[E:reaction.serious_top9]] [[E:reaction.serious_top10]]

At reaction-event level, recovered/resolved was recorded 1,280 times, unknown 1,033 times, not recovered/not resolved/ongoing 536 times, recovering/resolving 406 times, fatal 134 times, and recovered/resolved with sequelae 34 times. [[E:outcome.event.recovered_resolved]] [[E:outcome.event.unknown]] [[E:outcome.event.not_recovered_not_resolved_ongoing]] [[E:outcome.event.recovering_resolving]] [[E:outcome.event.fatal]] [[E:outcome.event.recovered_resolved_with_sequelae]] Because a case may contain multiple reactions, outcome-event counts are not case counts. [[E:outcome.multilabel_note]]

## Serious Cases / 15-Day Alert Assessment

A total of 1,023 cases were classified as serious. [[E:case.serious]] The seriousness flags included death in 68 cases, life-threatening in 105, hospitalization in 482, disabling in 44, congenital anomaly in 7, and other medically important criteria in 905. [[E:seriousness.death]] [[E:seriousness.life_threatening]] [[E:seriousness.hospitalization]] [[E:seriousness.disabling]] [[E:seriousness.congenital_anomaly]] [[E:seriousness.other_medically_important]]

The field fulfillexpeditecriteria was marked 'yes' for 1,023 cases (99.9%) and 'no' for 1. [[E:expedite.yes]] [[E:expedite.pct]] [[E:expedite.no]] This prototype does not equate that flag with a verified 15-day Alert submission because the supplied data does not provide explicit expectedness/listedness or a 15-day submission date. [[E:expedite.limitations]]

## Trends and Important Observations

Distinct-case volume peaked in 2025-07 at 109 cases, while the lowest full calendar month was 2025-08 at 64 cases. [[E:trend.peak_month]] [[E:trend.lowest_full_month]] The first and last calendar months are partial because the reporting interval does not align exactly to month boundaries. [[E:trend.boundary_note]]

For the five most common reactions, monthly maxima were: Acute kidney injury: 9 case(s) in 2025-01, 2025-03, 2025-08; Drug ineffective: 10 case(s) in 2025-08; Hypotension: 8 case(s) in 2025-08; Drug interaction: 6 case(s) in 2025-03; Dyspnoea: 6 case(s) in 2025-08. [[E:trend.reaction_peaks]]

Patients aged 65 years or older accounted for 674 cases (65.8% of all cases and 71.9% of cases with usable age). [[E:age.65plus]] [[E:age.65plus_pct_all]] [[E:age.65plus_pct_known]] These patterns are descriptive and should be reviewed by a qualified safety professional rather than treated automatically as safety signals.

## History of Actions

No structured safety-action history or supporting action document was supplied with the challenge inputs. This does not establish that no safety-related actions occurred. [[E:actions.statement]]

## Deterministic Supporting Tables

### Monthly case volume

| Received month | Unique cases |
| --- | --- |
| 2024-12 | 21 |
| 2025-01 | 75 |
| 2025-02 | 94 |
| 2025-03 | 83 |
| 2025-04 | 78 |
| 2025-05 | 80 |
| 2025-06 | 84 |
| 2025-07 | 109 |
| 2025-08 | 64 |
| 2025-09 | 76 |
| 2025-10 | 102 |
| 2025-11 | 75 |
| 2025-12 | 83 |

### Top reactions (distinct cases)

| Reaction / MedDRA PT | Cases | % of cases |
| --- | --- | --- |
| Acute kidney injury | 80 | 7.8% |
| Drug ineffective | 54 | 5.3% |
| Hypotension | 46 | 4.5% |
| Drug interaction | 43 | 4.2% |
| Dyspnoea | 38 | 3.7% |
| Bradycardia | 37 | 3.6% |
| Dizziness | 36 | 3.5% |
| Fatigue | 33 | 3.2% |
| Off label use | 31 | 3.0% |
| Fall | 30 | 2.9% |
| Diarrhoea | 30 | 2.9% |
| Condition aggravated | 27 | 2.6% |
| Hypokalaemia | 27 | 2.6% |
| Medication error | 25 | 2.4% |
| Asthenia | 25 | 2.4% |

### Age distribution

| Age band | Cases |
| --- | --- |
| <18 | 16 |
| 18-44 | 44 |
| 45-64 | 204 |
| 65-74 | 266 |
| 75+ | 408 |
| Unknown | 86 |

### Sex distribution

| Sex | Cases |
| --- | --- |
| female | 503 |
| male | 493 |
| unknown | 28 |

### Leading geography categories

| occurcountry category | Cases | % of cases |
| --- | --- | --- |
| eu | 342 | 33.4% |
| united kingdom | 278 | 27.1% |
| france | 185 | 18.1% |
| canada | 55 | 5.4% |
| italy | 51 | 5.0% |
| germany | 33 | 3.2% |
| spain | 24 | 2.3% |
| poland | 18 | 1.8% |
| portugal | 8 | 0.8% |
| Unknown | 7 | 0.7% |
| united states | 4 | 0.4% |
| IE | 3 | 0.3% |

## Case Index / Listing

A structured listing of all 1,024 de-duplicated cases is provided in `case_listing.csv`. It contains case ID, latest version, reactions, seriousness, received date, occurcountry, and reported reaction outcomes.

## Traceability

Generated narrative claims use `[[E:...]]` markers. The corresponding values and provenance are stored in `artifacts/evidence_catalog.json`. Section-scoped packets are stored in `artifacts/section_packets.json`.

## Data Limitations

- The source is a flattened safety dataset; follow-up versions were de-duplicated by selecting the highest `safetyreportversion` for each `safetyreportid`.
- `occurcountry` mixes country labels with the aggregate value `eu`; geography is therefore reported as source categories rather than normalized countries.
- Age is missing or unusable for some cases; percentages are labeled according to the denominator used.
- The dataset does not provide explicit expectedness/listedness or 15-day submission dates. `fulfillexpeditecriteria` is therefore not treated as proof of a verified 15-day Alert submission.
- No safety-action history source was supplied; absence of supplied action data does not mean no actions occurred.
- Counts are report counts, not incidence rates; exposure denominators are not supplied.
