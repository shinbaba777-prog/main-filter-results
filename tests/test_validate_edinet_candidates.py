import unittest

from scripts.validate_edinet_candidates import is_annual_context
from scripts.build_edinet_core_metric_review import is_annual_context as is_review_annual_context


class AnnualContextValidationTests(unittest.TestCase):
    def test_current_and_prior_annual_duration_contexts_are_recognized(self):
        for context in (
            "CurrentYearDuration",
            "Prior1YearDuration",
            "Prior2YearDuration",
            "Prior3YearDuration",
            "Prior4YearDuration",
        ):
            with self.subTest(context=context):
                self.assertTrue(is_annual_context(context))

    def test_annual_instant_contexts_are_recognized(self):
        for context in (
            "CurrentYearInstant",
            "Prior1YearInstant",
            "Prior2YearInstant",
            "Prior3YearInstant",
            "Prior4YearInstant",
        ):
            with self.subTest(context=context):
                self.assertTrue(is_annual_context(context))

    def test_annual_context_member_suffix_is_reviewable(self):
        self.assertTrue(
            is_annual_context("CurrentYearDuration_NonConsolidatedMember")
        )
        self.assertTrue(
            is_annual_context("Prior4YearInstant_ExampleMember")
        )

    def test_non_annual_contexts_are_not_misclassified(self):
        for context in (
            "",
            "CurrentQuarterDuration",
            "CurrentYTDDuration",
            "Prior5YearDuration",
            "RandomContext",
        ):
            with self.subTest(context=context):
                self.assertFalse(is_annual_context(context))

    def test_review_queue_allows_only_expected_annual_context_shapes(self):
        self.assertTrue(
            is_review_annual_context("CurrentYearDuration")
        )
        self.assertTrue(
            is_review_annual_context("Prior4YearDuration_NonConsolidatedMember")
        )
        self.assertFalse(
            is_review_annual_context("CurrentYearDuration_ConsolidatedMember")
        )
        self.assertFalse(
            is_review_annual_context("CurrentQuarterDuration")
        )


if __name__ == "__main__":
    unittest.main()
