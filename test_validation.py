"""
CCCS 106: Application Development and Emerging Technologies
Automated Unit Test Suite for Week 5 Form Validation Engine
Instructor: Allan O. Ibo, Jr., MSc

Executes comprehensive edge-case testing against ScholarshipValidator and
ScholarshipApplicant domain contracts without requiring a GUI window.
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
    """Test suite covering all domain validation rules and regex edge cases."""

    # ------------------------------------------------------------------------
    # 1. FULL NAME VALIDATION
    # ------------------------------------------------------------------------
    def test_valid_name(self):
        self.assertEqual(ScholarshipValidator.validate_name("Juan Dela Cruz"), "Juan Dela Cruz")
        self.assertEqual(ScholarshipValidator.validate_name("  Maria Clara O. Santos  "), "Maria Clara O. Santos")
        self.assertEqual(ScholarshipValidator.validate_name("Jean-Luc Picard"), "Jean-Luc Picard")

    def test_invalid_name_empty(self):
        with self.assertRaises(ScholarshipValidationError):
            ScholarshipValidator.validate_name("")
        with self.assertRaises(ScholarshipValidationError):
            ScholarshipValidator.validate_name("    ")

    def test_invalid_name_length_and_symbols(self):
        with self.assertRaises(ScholarshipValidationError):
            ScholarshipValidator.validate_name("A")  # Under 2 characters
        with self.assertRaises(ScholarshipValidationError):
            ScholarshipValidator.validate_name("Juan123")  # Contains digits
        with self.assertRaises(ScholarshipValidationError):
            ScholarshipValidator.validate_name("Juan <script>")  # Malicious tags

    # ------------------------------------------------------------------------
    # 2. STUDENT ID VALIDATION
    # ------------------------------------------------------------------------
    def test_valid_student_id(self):
        self.assertEqual(ScholarshipValidator.validate_student_id("2024-0123"), "2024-0123")
        self.assertEqual(ScholarshipValidator.validate_student_id(" 2025-10456 "), "2025-10456")

    def test_invalid_student_id_format(self):
        with self.assertRaises(IDFormatError):
            ScholarshipValidator.validate_student_id("24-0123")  # Missing 20XX
        with self.assertRaises(IDFormatError):
            ScholarshipValidator.validate_student_id("2024_0123")  # Underscore instead of hyphen
        with self.assertRaises(IDFormatError):
            ScholarshipValidator.validate_student_id("abcd-1234")  # Letters in year
        with self.assertRaises(IDFormatError):
            ScholarshipValidator.validate_student_id("")  # Empty

    # ------------------------------------------------------------------------
    # 3. INSTITUTIONAL EMAIL VALIDATION
    # ------------------------------------------------------------------------
    def test_valid_email(self):
        self.assertEqual(
            ScholarshipValidator.validate_email("mclara.santos@cspc.edu.ph"),
            "mclara.santos@cspc.edu.ph"
        )
        self.assertEqual(
            ScholarshipValidator.validate_email("  JUAN.DELACRUZ@CSPC.EDU.PH "),
            "juan.delacruz@cspc.edu.ph"
        )

    def test_invalid_email_domain(self):
        with self.assertRaises(EmailDomainError):
            ScholarshipValidator.validate_email("juan@gmail.com")
        with self.assertRaises(EmailDomainError):
            ScholarshipValidator.validate_email("juan@cspc.edu.com")
        with self.assertRaises(EmailDomainError):
            ScholarshipValidator.validate_email("not-an-email")
        with self.assertRaises(EmailDomainError):
            ScholarshipValidator.validate_email("")

    # ------------------------------------------------------------------------
    # 4. PHILIPPINE MOBILE PHONE VALIDATION & NORMALIZATION
    # ------------------------------------------------------------------------
    def test_valid_phone_normalization(self):
        # 09 local format
        self.assertEqual(ScholarshipValidator.validate_phone("09181234567"), "09181234567")
        # International +63 format converted to 09
        self.assertEqual(ScholarshipValidator.validate_phone("+639181234567"), "09181234567")
        # Formatted with spaces and hyphens
        self.assertEqual(ScholarshipValidator.validate_phone("  +63 918-123-4567  "), "09181234567")

    def test_invalid_phone_numbers(self):
        with self.assertRaises(ScholarshipValidationError):
            ScholarshipValidator.validate_phone("08123456789")  # Non-09 prefix
        with self.assertRaises(ScholarshipValidationError):
            ScholarshipValidator.validate_phone("0918123456")  # Too short (10 digits)
        with self.assertRaises(ScholarshipValidationError):
            ScholarshipValidator.validate_phone("091812345678")  # Too long (12 digits)
        with self.assertRaises(ScholarshipValidationError):
            ScholarshipValidator.validate_phone("abcdefghijk")

    # ------------------------------------------------------------------------
    # 5. GWA NUMERIC & RANGE VALIDATION
    # ------------------------------------------------------------------------
    def test_valid_gwa(self):
        self.assertEqual(ScholarshipValidator.validate_gwa("1.00"), 1.00)
        self.assertEqual(ScholarshipValidator.validate_gwa(" 1.45 "), 1.45)
        self.assertEqual(ScholarshipValidator.validate_gwa("5.00"), 5.00)

    def test_invalid_gwa_out_of_bounds(self):
        with self.assertRaises(GWARangeError):
            ScholarshipValidator.validate_gwa("0.95")  # Beyond highest honor
        with self.assertRaises(GWARangeError):
            ScholarshipValidator.validate_gwa("5.25")  # Beyond failing bound
        with self.assertRaises(GWARangeError):
            ScholarshipValidator.validate_gwa("-1.50")

    def test_invalid_gwa_non_numeric(self):
        with self.assertRaises(GWARangeError):
            ScholarshipValidator.validate_gwa("uno")
        with self.assertRaises(GWARangeError):
            ScholarshipValidator.validate_gwa("1.45GPA")
        with self.assertRaises(GWARangeError):
            ScholarshipValidator.validate_gwa("")

    # ------------------------------------------------------------------------
    # 6. DOMAIN CONTRACT (@DATACLASS) IMMUTABILITY
    # ------------------------------------------------------------------------
    def test_dataclass_contract_creation(self):
        applicant = ScholarshipApplicant(
            full_name="Maria Clara Santos",
            student_id="2024-0891",
            email="mclara.santos@cspc.edu.ph",
            phone="09181234567",
            gwa=1.45,
            program="DOST Science & Technology Scholarship"
        )
        self.assertEqual(applicant.full_name, "Maria Clara Santos")
        self.assertEqual(applicant.gwa, 1.45)

        # Frozen contract test (mutation must raise FrozenInstanceError)
        with self.assertRaises(Exception):
            applicant.gwa = 1.00

    # ------------------------------------------------------------------------
    # 7. GUI EVENT FLOW INTEGRATION TEST (MOCK RUNNER)
    # ------------------------------------------------------------------------
    def test_gui_submission_flow(self):
        from unittest.mock import MagicMock
        import flet as ft
        import scholarship_portal

        mock_page = MagicMock()
        mock_page.window = MagicMock()
        mock_page.show_dialog = MagicMock()
        mock_page.update = MagicMock()

        # Initialize GUI
        scholarship_portal.main(mock_page)

        col = mock_page.add.call_args[0][0]
        submit_btn = next(c for c in col.controls if isinstance(c, ft.FilledButton))
        name_field = col.controls[2]
        id_field = col.controls[3]
        email_field = col.controls[4]
        phone_field = col.controls[5]
        gwa_field = col.controls[6]
        program_dropdown = col.controls[7]

        # Trigger submission on invalid empty fields
        submit_btn.on_click(MagicMock())
        self.assertIsNotNone(name_field.error)
        self.assertTrue(mock_page.show_dialog.called)

        # Populate valid applicant data
        name_field.value = "Maria Clara Santos"
        id_field.value = "2024-0891"
        email_field.value = "mclara.santos@cspc.edu.ph"
        phone_field.value = "09181234567"
        gwa_field.value = "1.45"
        program_dropdown.value = "DOST Science & Technology Scholarship"

        # Trigger valid submission (builds dataclass and card with ft.Border.all)
        mock_page.show_dialog.reset_mock()
        submit_btn.on_click(MagicMock())
        self.assertIsNone(name_field.error)
        self.assertTrue(mock_page.show_dialog.called)


if __name__ == "__main__":
    unittest.main()
