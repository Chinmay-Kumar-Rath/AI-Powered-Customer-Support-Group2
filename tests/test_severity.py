
import unittest

from ml.classifier import classify_severity, classify


class TestSeverityClassification(unittest.TestCase):
    """Tests for severity classification and priority mapping."""

    def test_critical_production_outage(self):
        severity, confidence = classify_severity(
            "The production system is down for all users."
        )
        self.assertEqual(severity, "Critical")
        self.assertGreater(confidence, 0)

    def test_high_team_access_problem(self):
        severity, _ = classify_severity(
            "The entire team cannot access the system."
        )
        self.assertEqual(severity, "High")

    def test_medium_individual_access_problem(self):
        severity, _ = classify_severity(
            "One user cannot access the application."
        )
        self.assertEqual(severity, "Medium")

    def test_low_routine_request(self):
        severity, _ = classify_severity(
            "This is a routine request for software installation."
        )
        self.assertEqual(severity, "Low")

    def test_negated_critical_word(self):
        severity, _ = classify_severity(
            "This is not a critical issue."
        )
        self.assertEqual(severity, "Medium")

    def test_critical_security_incident(self):
        severity, _ = classify_severity(
            "We have a critical security incident."
        )
        self.assertEqual(severity, "Critical")

    def test_priority_mapping(self):
        cases = [
            (
                "Production outage",
                "The production system is down for all users.",
                "Critical",
                "P1",
            ),
            (
                "Team access problem",
                "The entire team cannot access the system.",
                "High",
                "P2",
            ),
            (
                "Individual access problem",
                "One user cannot access the application.",
                "Medium",
                "P3",
            ),
            (
                "Routine installation",
                "This is a routine request for software installation.",
                "Low",
                "P4",
            ),
        ]

        for subject, description, expected_severity, expected_priority in cases:
            with self.subTest(subject=subject):
                result = classify(subject, description)
                self.assertEqual(result["severity"], expected_severity)
                self.assertEqual(result["priority"], expected_priority)

    def test_informational_email_signature_question_is_low(self):
        severity, _ = classify_severity(
            "Could you explain how to change my email signature?"
        )
        self.assertEqual(severity, "Low")

    def test_potential_data_breach_needs_review(self):
        severity, _ = classify_severity(
            "A potential breach may have exposed medical records."
        )
        self.assertEqual(severity, "Unknown")

    def test_production_system_down_for_all_users_is_critical(self):
        severity, _ = classify_severity(
            "Production system is down for all users."
        )
        self.assertEqual(severity, "Critical")

    def test_several_employees_network_access_is_high(self):
        severity, _ = classify_severity(
            "Several employees cannot access the network."
        )
        self.assertEqual(severity, "High")


if __name__ == "__main__":
    unittest.main()
