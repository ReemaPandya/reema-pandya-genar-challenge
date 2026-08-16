import sys
import types
import unittest
from unittest.mock import patch

from src.genar.cli import build_arg_parser
from src.genar.generator import GeminiSectionGenerator
from src.genar.loader import deduplicate_latest, parse_reactions
from src.genar.validation import validate_markers, validate_prohibited_claims


class PipelineTests(unittest.TestCase):
    def test_latest_version_wins(self):
        rows = [
            {"safetyreportid": 1, "safetyreportversion": 1, "receivedate": 20250101, "serious": "serious", "patient_patientsex": "female", "occurcountry": "x", "patient_reaction_reactionmeddraversionpt": "27.1", "patient_reaction_reactionmeddrapt": "Old term", "patient_reaction_reactionoutcome": "unknown", "fulfillexpeditecriteria": "yes"},
            {"safetyreportid": 1, "safetyreportversion": 2, "receivedate": 20250101, "serious": "serious", "patient_patientsex": "female", "occurcountry": "x", "patient_reaction_reactionmeddraversionpt": "27.1", "patient_reaction_reactionmeddrapt": "New term", "patient_reaction_reactionoutcome": "recovered/resolved", "fulfillexpeditecriteria": "yes"},
        ]
        cases, audit = deduplicate_latest(rows)
        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0]["safetyreportversion"], 2)
        self.assertEqual(audit["followup_rows_removed"], 1)

    def test_comma_meddra_pt_alignment(self):
        row = {"patient_reaction_reactionmeddraversionpt": "27.1,27.1", "patient_reaction_reactionmeddrapt": "Hallucination, visual,Fall"}
        self.assertEqual(parse_reactions(row), ["Hallucination, visual", "Fall"])

    def test_unknown_marker_rejected(self):
        packet = {"case.total": {"value": 10, "provenance": "test"}}
        self.assertTrue(validate_markers("There were 10 cases. [[E:not.real]]", packet))

    def test_unsupported_safety_conclusion_rejected(self):
        self.assertTrue(validate_prohibited_claims("No safety concerns were identified.", "narrative_summary"))

    def test_cli_defaults_to_gemini_and_human_review(self):
        args = build_arg_parser().parse_args(["--data", "input.xlsx"])
        self.assertEqual(args.provider, "gemini")
        self.assertEqual(args.model, "gemini-3.5-flash")
        self.assertEqual(args.review, "interactive")

    def test_gemini_adapter_uses_scoped_context_and_system_instruction(self):
        calls = {}

        class FakeConfig:
            def __init__(self, **kwargs):
                calls["config"] = kwargs

        class FakeModels:
            def generate_content(self, **kwargs):
                calls["request"] = kwargs
                return types.SimpleNamespace(text="10 cases were observed. [[E:case.total]]")

        class FakeClient:
            def __init__(self):
                self.models = FakeModels()

        fake_google = types.ModuleType("google")
        fake_genai = types.ModuleType("google.genai")
        fake_genai.Client = FakeClient
        class FakeAFC:
            def __init__(self, **kwargs):
                calls["afc"] = kwargs

        fake_genai.types = types.SimpleNamespace(
            GenerateContentConfig=FakeConfig,
            AutomaticFunctionCallingConfig=FakeAFC,
        )
        fake_google.genai = fake_genai

        with patch.dict(sys.modules, {"google": fake_google, "google.genai": fake_genai}):
            result = GeminiSectionGenerator(model="gemini-test").generate(
                "summary_cases",
                {"case.total": {"value": 10, "provenance": "unit test"}},
                "SYSTEM RULE",
                "SECTION RULE",
            )

        self.assertIn("[[E:case.total]]", result)
        self.assertEqual(calls["request"]["model"], "gemini-test")
        self.assertIn("case.total", calls["request"]["contents"])
        self.assertEqual(calls["config"]["system_instruction"], "SYSTEM RULE")
        self.assertEqual(calls["config"]["temperature"], 0.0)
        self.assertEqual(calls["afc"]["disable"], True)


if __name__ == "__main__":
    unittest.main()
