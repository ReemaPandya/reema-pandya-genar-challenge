from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from .prompts import build_context


class SectionGenerator(Protocol):
    name: str
    model: str

    def generate(
        self,
        section: str,
        packet: dict[str, Any],
        system: str,
        rule: str,
        correction: str | None = None,
    ) -> str: ...


@dataclass
class GeminiSectionGenerator:
    """Gemini Developer API adapter with free-tier rate limiting."""

    model: str = "gemini-3.5-flash"
    name: str = "gemini-developer-api"
    temperature: float = 0.0
    max_output_tokens: int = 5000

    # Stay safely below a 5 requests/minute free-tier limit.
    min_request_interval_seconds: float = 15.0

    _last_request_at: float = field(
        default=0.0,
        init=False,
        repr=False,
    )

    def _throttle(self) -> None:
        if self._last_request_at == 0:
            return

        elapsed = time.monotonic() - self._last_request_at

        if elapsed < self.min_request_interval_seconds:
            time.sleep(
                self.min_request_interval_seconds - elapsed
            )

    def generate(
        self,
        section: str,
        packet: dict[str, Any],
        system: str,
        rule: str,
        correction: str | None = None,
    ) -> str:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError(
                "Gemini provider requires the google-genai package. "
                "Run: pip install -r requirements.txt"
            ) from exc

        self._throttle()

        client = genai.Client()

        print(f"Generating {section} with Gemini...")

        self._last_request_at = time.monotonic()

        response = client.models.generate_content(
            model=self.model,
            contents=build_context(
                section,
                packet,
                rule,
                correction=correction,
            ),
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
                automatic_function_calling=
                    types.AutomaticFunctionCallingConfig(
                        disable=True
                    ),
            ),
        )

        text = (response.text or "").strip()

        if not text:
            raise RuntimeError(
                f"Gemini returned an empty response "
                f"for section {section!r}"
            )

        return text

@dataclass
class TemplateGenerator:
    """Credential-free deterministic fallback used for tests and reproducible review.

    This is deliberately not represented as AI. The exact same section evidence packets
    can be sent to Gemini through GeminiSectionGenerator.
    """

    name: str = "grounded-template"
    model: str = "none"

    @staticmethod
    def _v(packet: dict[str, Any], key: str) -> Any:
        return packet[key]["value"]

    def generate(
        self,
        section: str,
        packet: dict[str, Any],
        system: str,
        rule: str,
        correction: str | None = None,
    ) -> str:
        v = lambda k: self._v(packet, k)
        if section == "narrative_summary":
            t1, t2, t3 = v("reaction.top1"), v("reaction.top2"), v("reaction.top3")
            g1, g2, g3 = v("geo.top1"), v("geo.top2"), v("geo.top3")
            peak = v("trend.peak_month")
            low = v("trend.lowest_full_month")
            return (
                f"During the reporting period, {v('case.total'):,} unique cases were identified after case-version de-duplication; "
                f"{v('case.serious'):,} ({v('case.serious_pct')}%) were classified as serious and {v('case.non_serious'):,} as non-serious. [[E:case.total]] [[E:case.serious]] [[E:case.serious_pct]] [[E:case.non_serious]]\n\n"
                f"Patients aged 65 years or older accounted for {v('age.65plus'):,} cases ({v('age.65plus_pct_all')}% of all cases; {v('age.65plus_pct_known')}% among cases with usable age). [[E:age.65plus]] [[E:age.65plus_pct_all]] [[E:age.65plus_pct_known]] "
                f"The sex distribution included {v('sex.female'):,} female, {v('sex.male'):,} male, and {v('sex.unknown'):,} unknown-sex cases. [[E:sex.female]] [[E:sex.male]] [[E:sex.unknown]]\n\n"
                f"The leading occurcountry categories were {g1['location']} ({g1['cases']:,}), {g2['location']} ({g2['cases']:,}), and {g3['location']} ({g3['cases']:,}). [[E:geo.top1]] [[E:geo.top2]] [[E:geo.top3]] "
                "The geography field mixes country and aggregate-region labels, so these categories should not be interpreted as a harmonized country taxonomy. [[E:geo.mixed_granularity]]\n\n"
                f"The most frequently reported reactions at distinct-case level were {t1['reaction']} ({t1['cases']:,} cases), {t2['reaction']} ({t2['cases']:,}), and {t3['reaction']} ({t3['cases']:,}). [[E:reaction.top1]] [[E:reaction.top2]] [[E:reaction.top3]] "
                f"Calendar-month case volume was highest in {peak['month']} with {peak['cases']:,} cases; the lowest full calendar month was {low['month']} with {low['cases']:,} cases. [[E:trend.peak_month]] [[E:trend.lowest_full_month]] "
                "These are descriptive observations and are not, by themselves, evidence of a safety signal."
            )
        if section == "summary_cases":
            g = [v(f"geo.top{i}") for i in range(1, 6)]
            return (
                f"The source contained {v('source.rows'):,} rows. Selecting the highest safetyreportversion for each safetyreportid removed {v('source.followups_removed'):,} follow-up rows from case-level counting and yielded {v('case.total'):,} unique cases. [[E:source.rows]] [[E:source.followups_removed]] [[E:case.total]]\n\n"
                f"Serious cases: {v('case.serious'):,}; non-serious cases: {v('case.non_serious'):,}. [[E:case.serious]] [[E:case.non_serious]]\n\n"
                f"Age bands were <18: {v('age.lt18'):,}; 18-44: {v('age.18_44'):,}; 45-64: {v('age.45_64'):,}; 65-74: {v('age.65_74'):,}; 75+: {v('age.75plus'):,}; unknown/unusable: {v('age.unknown'):,}. [[E:age.lt18]] [[E:age.18_44]] [[E:age.45_64]] [[E:age.65_74]] [[E:age.75plus]] [[E:age.unknown]]\n\n"
                f"Sex was reported as female in {v('sex.female'):,} cases, male in {v('sex.male'):,}, and unknown in {v('sex.unknown'):,}. [[E:sex.female]] [[E:sex.male]] [[E:sex.unknown]]\n\n"
                + "The five largest occurcountry categories were "
                + ", ".join(f"{x['location']} ({x['cases']:,})" for x in g)
                + ". [[E:geo.top1]] [[E:geo.top2]] [[E:geo.top3]] [[E:geo.top4]] [[E:geo.top5]]"
            )
        if section == "reaction_analysis":
            top = [v(f"reaction.top{i}") for i in range(1, 11)]
            serious = [v(f"reaction.serious_top{i}") for i in range(1, 11)]
            top_text = ", ".join(f"{x['reaction']} ({x['cases']})" for x in top)
            serious_text = ", ".join(f"{x['reaction']} ({x['serious_cases']})" for x in serious)
            return (
                "At distinct-case level, the ten most frequently reported reactions were: "
                + top_text
                + ". "
                + " ".join(f"[[E:reaction.top{i}]]" for i in range(1, 11))
                + "\n\n"
                + "Among serious cases, the ten most frequently reported reactions were: "
                + serious_text
                + ". "
                + " ".join(f"[[E:reaction.serious_top{i}]]" for i in range(1, 11))
                + "\n\n"
                + f"At reaction-event level, recovered/resolved was recorded {v('outcome.event.recovered_resolved'):,} times, unknown {v('outcome.event.unknown'):,} times, not recovered/not resolved/ongoing {v('outcome.event.not_recovered_not_resolved_ongoing'):,} times, recovering/resolving {v('outcome.event.recovering_resolving'):,} times, fatal {v('outcome.event.fatal'):,} times, and recovered/resolved with sequelae {v('outcome.event.recovered_resolved_with_sequelae'):,} times. [[E:outcome.event.recovered_resolved]] [[E:outcome.event.unknown]] [[E:outcome.event.not_recovered_not_resolved_ongoing]] [[E:outcome.event.recovering_resolving]] [[E:outcome.event.fatal]] [[E:outcome.event.recovered_resolved_with_sequelae]] "
                + "Because a case may contain multiple reactions, outcome-event counts are not case counts. [[E:outcome.multilabel_note]]"
            )
        if section == "serious_alerts":
            return (
                f"A total of {v('case.serious'):,} cases were classified as serious. [[E:case.serious]] "
                f"The seriousness flags included death in {v('seriousness.death'):,} cases, life-threatening in {v('seriousness.life_threatening'):,}, hospitalization in {v('seriousness.hospitalization'):,}, disabling in {v('seriousness.disabling'):,}, congenital anomaly in {v('seriousness.congenital_anomaly'):,}, and other medically important criteria in {v('seriousness.other_medically_important'):,}. [[E:seriousness.death]] [[E:seriousness.life_threatening]] [[E:seriousness.hospitalization]] [[E:seriousness.disabling]] [[E:seriousness.congenital_anomaly]] [[E:seriousness.other_medically_important]]\n\n"
                f"The field fulfillexpeditecriteria was marked 'yes' for {v('expedite.yes'):,} cases ({v('expedite.pct')}%) and 'no' for {v('expedite.no'):,}. [[E:expedite.yes]] [[E:expedite.pct]] [[E:expedite.no]] "
                "This prototype does not equate that flag with a verified 15-day Alert submission because the supplied data does not provide explicit expectedness/listedness or a 15-day submission date. [[E:expedite.limitations]]"
            )
        if section == "trends":
            peak = v("trend.peak_month")
            low = v("trend.lowest_full_month")
            peaks = v("trend.reaction_peaks")
            rx = "; ".join(
                f"{x['reaction']}: {x['peak_cases']} case(s) in {', '.join(x['peak_months'])}" for x in peaks
            )
            return (
                f"Distinct-case volume peaked in {peak['month']} at {peak['cases']:,} cases, while the lowest full calendar month was {low['month']} at {low['cases']:,} cases. [[E:trend.peak_month]] [[E:trend.lowest_full_month]] "
                "The first and last calendar months are partial because the reporting interval does not align exactly to month boundaries. [[E:trend.boundary_note]]\n\n"
                f"For the five most common reactions, monthly maxima were: {rx}. [[E:trend.reaction_peaks]]\n\n"
                f"Patients aged 65 years or older accounted for {v('age.65plus'):,} cases ({v('age.65plus_pct_all')}% of all cases and {v('age.65plus_pct_known')}% of cases with usable age). [[E:age.65plus]] [[E:age.65plus_pct_all]] [[E:age.65plus_pct_known]] "
                "These patterns are descriptive and should be reviewed by a qualified safety professional rather than treated automatically as safety signals."
            )
        if section == "history_actions":
            return (
                "No structured safety-action history or supporting action document was supplied with the challenge inputs. "
                "This does not establish that no safety-related actions occurred. [[E:actions.statement]]"
            )
        raise KeyError(section)
