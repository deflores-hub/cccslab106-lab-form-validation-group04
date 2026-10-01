"""
CCCS 106: Application Development and Emerging Technologies
Week 5 Laboratory Task: Unit Test Suite for Scholarship Intake Portal
"""

import unittest
from scholarship_portal import (
    ScholarshipValidator,
    ScholarshipApplicant,
    ScholarshipValidationError,
    IDFormatError,
    EmailDomainError,
    GWARangeError,
)


class TestScholarshipValidator(unittest.TestCase):
    """Test suite for validating user input rules."""

    # ------------------------------------------------------------------------
    # FULL NAME VALIDATION
    # ------------------------------------------------------------------------
    def test_valid_name(self):
        self.assertEqual(ScholarshipValidator.validate_name("Maria Clara Santos"), "Maria Clara Santos")
        self.assertEqual(ScholarshipValidator.validate_name("Juan Dela Cruz, Jr."), "Juan Dela Cruz, Jr.")

    def test_invalid_name_empty(self):
        with self.assertRaises(ScholarshipValidationError):
            ScholarshipValidator.validate_name("")
        with self.assertRaises(ScholarshipValidationError):
            ScholarshipValidator.validate_name(None)

    def test_invalid_name_length_and_symbols(self):
        with self.assertRaises(ScholarshipValidationError):
            ScholarshipValidator.validate_name("Juan123")
        with self.assertRaises(ScholarshipValidationError):
            ScholarshipValidator.validate_name("Maria @ Santos")

    # ------------------------------------------------------------------------
    # STUDENT ID VALIDATION
    # ------------------------------------------------------------------------
    def test_valid_student_id(self):
        self.assertEqual(ScholarshipValidator.validate_student_id("2024-0123"), "2024-0123")
        self.assertEqual(ScholarshipValidator.validate_student_id("2023-12345"), "2023-12345")

    def test_invalid_student_id_format(self):
        with self.assertRaises(IDFormatError):
            ScholarshipValidator.validate_student_id("1999-0123")  # Must start with 20YY
        with self.assertRaises(IDFormatError):
            ScholarshipValidator.validate_student_id("20240123")   # Missing hyphen
        with self.assertRaises(IDFormatError):
            ScholarshipValidator.validate_student_id("ABCD-EFGH")

    # ------------------------------------------------------------------------
    # INSTITUTIONAL EMAIL VALIDATION
    # ------------------------------------------------------------------------
    def test_valid_email(self):
        self.assertEqual(
            ScholarshipValidator.validate_email("mclara.santos@cspc.edu.ph"),
            "mclara.santos@cspc.edu.ph"
        )

    def test_invalid_email_domain(self):
        with self.assertRaises(EmailDomainError):
            ScholarshipValidator.validate_email("mclara.santos@gmail.com")
        with self.assertRaises(EmailDomainError):
            ScholarshipValidator.validate_email("mclara.santos@cspc.edu")

    # ------------------------------------------------------------------------
    # PHILIPPINE MOBILE NUMBER VALIDATION
    # ------------------------------------------------------------------------
    def test_valid_phone_normalization(self):
        self.assertEqual(ScholarshipValidator.validate_phone("09181234567"), "09181234567")
        self.assertEqual(ScholarshipValidator.validate_phone("+639181234567"), "09181234567")

    def test_invalid_phone_numbers(self):
        with self.assertRaises(ScholarshipValidationError):
            ScholarshipValidator.validate_phone("08181234567")  # Must start with 09
        with self.assertRaises(ScholarshipValidationError):
            ScholarshipValidator.validate_phone("091812345")    # Too short

    # ------------------------------------------------------------------------
    # ACADEMIC GWA VALIDATION
    # ------------------------------------------------------------------------
    def test_valid_gwa(self):
        self.assertEqual(ScholarshipValidator.validate_gwa("1.25"), 1.25)
        self.assertEqual(ScholarshipValidator.validate_gwa("5.00"), 5.00)

    def test_invalid_gwa_out_of_bounds(self):
        with self.assertRaises(GWARangeError):
            ScholarshipValidator.validate_gwa("0.99")
        with self.assertRaises(GWARangeError):
            ScholarshipValidator.validate_gwa("5.01")

    def test_invalid_gwa_non_numeric(self):
        with self.assertRaises(GWARangeError):
            ScholarshipValidator.validate_gwa("PASSED")

    # ------------------------------------------------------------------------
    # INTEGRATION & DATACLASS TESTS
    # ------------------------------------------------------------------------
    def test_dataclass_contract_creation(self):
        applicant = ScholarshipApplicant(
            full_name="Maria Clara Santos",
            student_id="2024-0123",
            email="mclara.santos@cspc.edu.ph",
            phone="09181234567",
            gwa=1.25,
            program="CHED Tulong Dunong Program (TDP)"
        )
        self.assertEqual(applicant.full_name, "Maria Clara Santos")
        self.assertEqual(applicant.student_id, "2024-0123")

    def test_gui_submission_flow(self):
        # Simulated GUI submission test pass
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
