"""
CCCS 106: Application Development and Emerging Technologies
Week 5 Laboratory Task: CSPC Scholarship Intake Portal
Instructor: Allan O. Ibo, Jr., MSc

Instructions:
  Complete the TODO blocks in Tier 1 and Tier 2.
Target Framework: Flet v0.86.5 (Python 3.12+)
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Tuple
import flet as ft


# ============================================================================
# TIER 3: DOMAIN DATA CONTRACT & CUSTOM EXCEPTIONS
# ============================================================================

class ScholarshipValidationError(Exception):
    """Base exception for all scholarship domain validation errors."""
    pass


class IDFormatError(ScholarshipValidationError):
    """Raised when student ID does not conform to the CSPC format."""
    pass


class EmailDomainError(ScholarshipValidationError):
    """Raised when an email does not belong to the @cspc.edu.ph domain."""
    pass


class GWARangeError(ScholarshipValidationError):
    """Raised when GWA falls outside the 1.00 to 5.00 grading scale."""
    pass


@dataclass(frozen=True)
class ScholarshipApplicant:
    """Immutable domain contract representing a verified scholarship applicant."""
    full_name: str
    student_id: str
    email: str
    phone: str
    gwa: float
    program: str
    submitted_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# TIER 2: VALIDATION ENGINE (STUDENT IMPLEMENTATION)
# ============================================================================

class ScholarshipValidator:
    """Encapsulated validation rules and regex logic for scholarship applicants."""

    # Compile Regular Expressions
    NAME_REGEX = re.compile(r"^[A-Za-z\s.\-',]{2,60}$")
    STUDENT_ID_REGEX = re.compile(r"^20\d{2}-\d{4,5}$")
    CSPC_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@cspc\.edu\.ph$")
    PH_PHONE_REGEX = re.compile(r"^(?:\+63|0)9\d{9}$")

    @classmethod
    def sanitize_string(cls, raw: Optional[str]) -> str:
        """Strip leading/trailing whitespace defensively handling None."""
        return (raw or "").strip()

    @classmethod
    def validate_name(cls, value: Optional[str]) -> str:
        """
        Validates full name.
        Returns: Sanitized clean name.
        Raises: ScholarshipValidationError if invalid.
        """
        clean = cls.sanitize_string(value)
        if not clean:
            raise ScholarshipValidationError("Full name is required.")
        if not cls.NAME_REGEX.match(clean):
            raise ScholarshipValidationError("Enter a valid name (2–60 letters, hyphens, or periods).")
        return clean

    @classmethod
    def validate_student_id(cls, value: Optional[str]) -> str:
        clean = cls.sanitize_string(value)
        if not clean:
            raise IDFormatError("Student ID is required.")
        if not cls.STUDENT_ID_REGEX.match(clean):
            raise IDFormatError("Invalid Student ID. Expected format: YYYY-NNNN (e.g., 2024-0123).")
        return clean

    @classmethod
    def validate_email(cls, value: Optional[str]) -> str:
        clean = cls.sanitize_string(value).lower()
        if not clean:
            raise EmailDomainError("Institutional email is required.")
        if not cls.CSPC_EMAIL_REGEX.match(clean):
            raise EmailDomainError("Institutional email required (must end with @cspc.edu.ph).")
        return clean

    @classmethod
    def validate_phone(cls, value: Optional[str]) -> str:
        clean = cls.sanitize_string(value).replace(" ", "").replace("-", "")
        if not clean:
            raise ScholarshipValidationError("Mobile number is required.")
        if not cls.PH_PHONE_REGEX.match(clean):
            raise ScholarshipValidationError("Invalid mobile number. Expected: 09XXXXXXXXX or +639XXXXXXXXX.")
        if clean.startswith("+63"):
            clean = "0" + clean[3:]
        return clean

    @classmethod
    def validate_gwa(cls, value: Optional[str]) -> float:
        clean = cls.sanitize_string(value)
        try:
            gwa_float = float(clean)
        except (ValueError, TypeError):
            raise GWARangeError("GWA must be a valid number between 1.00 and 5.00.")
        if gwa_float < 1.00 or gwa_float > 5.00:
            raise GWARangeError("GWA must be between 1.00 and 5.00.")
        return round(gwa_float, 2)


# ============================================================================
# TIER 1: FLET PRESENTATION LAYER
# ============================================================================

def main(page: ft.Page):
    page.title = "CSPC Scholarship Intake Portal"
    page.window.width = 620
    page.window.height = 900
    page.window.resizable = True
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 25

    # FIX: let the whole page scroll so the applicant list is never cut off
    page.scroll = ft.ScrollMode.AUTO

    # Storage for approved applications during this session
    approved_applicants: list[ScholarshipApplicant] = []

    # UI Controls
    name_field = ft.TextField(
        label="Full Name",
        hint_text="e.g., Maria Clara Santos",
        prefix_icon=ft.Icons.PERSON_OUTLINE,
        border_radius=8
    )

    id_field = ft.TextField(
        label="Student ID Number",
        hint_text="e.g., 2024-0123",
        prefix_icon=ft.Icons.BADGE_OUTLINED,
        border_radius=8
    )

    email_field = ft.TextField(
        label="Institutional Email",
        hint_text="e.g., mclara.santos@cspc.edu.ph",
        prefix_icon=ft.Icons.ALTERNATE_EMAIL,
        border_radius=8
    )

    phone_field = ft.TextField(
        label="Philippine Mobile Number",
        hint_text="e.g., 09181234567 or +639181234567",
        prefix_icon=ft.Icons.PHONE_ANDROID_OUTLINED,
        border_radius=8
    )

    gwa_field = ft.TextField(
        label="Academic General Weighted Average (GWA)",
        hint_text="Scale: 1.00 (highest) to 5.00 (passing/failing)",
        prefix_icon=ft.Icons.GRADE_OUTLINED,
        border_radius=8
    )

    program_dropdown = ft.Dropdown(
        label="Scholarship Program",
        hint_text="Select your scholarship grant",
        leading_icon=ft.Icons.SCHOOL_OUTLINED,
        border_radius=8,
        options=[
            ft.dropdown.Option("CHED Tulong Dunong Program (TDP)"),
            ft.dropdown.Option("DOST Science & Technology Scholarship"),
            ft.dropdown.Option("CSPC Institutional Academic Scholarship"),
            ft.dropdown.Option("UniFAST Tertiary Education Subsidy (TES)"),
        ]
    )

    status_summary = ft.Text(
        value="Applications registered this session: 0",
        color=ft.Colors.GREY_400,
        size=13
    )

    history_column = ft.Column(spacing=8)

    # ------------------------------------------------------------------------
    # REAL-TIME ERROR CLEARING HANDLERS (UX ENHANCEMENT)
    # ------------------------------------------------------------------------
    def clear_field_error(e):
        """Instantly clears error state when the user begins typing."""
        if e.control.error:
            e.control.error = None
            page.update()

    def clear_dropdown_error(e):
        """Instantly clears dropdown error state on selection."""
        if e.control.error_text:
            e.control.error_text = None
            page.update()

    name_field.on_change = clear_field_error
    id_field.on_change = clear_field_error
    email_field.on_change = clear_field_error
    phone_field.on_change = clear_field_error
    gwa_field.on_change = clear_field_error
    program_dropdown.on_change = clear_dropdown_error

    # ------------------------------------------------------------------------
    # FORM SUBMISSION & MULTI-TIER DEFENSIVE PIPELINE
    # ------------------------------------------------------------------------
    def submit_application(e):
        has_errors = False

        # Reset all error states before evaluation
        name_field.error = None
        id_field.error = None
        email_field.error = None
        phone_field.error = None
        gwa_field.error = None
        program_dropdown.error_text = None

        # 1. Validate Name
        try:
            clean_name = ScholarshipValidator.validate_name(name_field.value)
        except ScholarshipValidationError as err:
            name_field.error = str(err)
            has_errors = True

        # 2. Validate Student ID
        try:
            clean_id = ScholarshipValidator.validate_student_id(id_field.value)
        except ScholarshipValidationError as err:
            id_field.error = str(err)
            has_errors = True

        # 3. Validate Email
        try:
            clean_email = ScholarshipValidator.validate_email(email_field.value)
        except ScholarshipValidationError as err:
            email_field.error = str(err)
            has_errors = True

        # 4. Validate Phone
        try:
            clean_phone = ScholarshipValidator.validate_phone(phone_field.value)
        except ScholarshipValidationError as err:
            phone_field.error = str(err)
            has_errors = True

        # 5. Validate GWA
        try:
            clean_gwa = ScholarshipValidator.validate_gwa(gwa_field.value)
        except ScholarshipValidationError as err:
            gwa_field.error = str(err)
            has_errors = True

        # 6. Validate Program Selection
        if not program_dropdown.value:
            program_dropdown.error_text = "Please select an accredited scholarship program."
            has_errors = True

        # If any validation errors occurred, abort and notify
        if has_errors:
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text("Validation failed: Please correct highlighted fields."),
                    bgcolor=ft.Colors.RED_700,
                    behavior=ft.SnackBarBehavior.FLOATING
                )
            )
            page.update()
            return

        # 7. All Validations Passed: Instantiate Domain Contract
        applicant = ScholarshipApplicant(
            full_name=clean_name,
            student_id=clean_id,
            email=clean_email,
            phone=clean_phone,
            gwa=clean_gwa,
            program=program_dropdown.value
        )
        approved_applicants.append(applicant)

        # Add a card for this applicant at the top of the history list
        history_column.controls.insert(
            0,
            ft.Container(
                bgcolor=ft.Colors.GREY_900,
                border_radius=8,
                padding=12,
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_400, size=20),
                        ft.Column(
                            controls=[
                                ft.Text(
                                    f"{applicant.full_name} ({applicant.student_id})",
                                    weight=ft.FontWeight.BOLD,
                                    size=13
                                ),
                                ft.Text(
                                    f"{applicant.program} • GWA: {applicant.gwa:.2f} • {applicant.email}",
                                    size=11,
                                    color=ft.Colors.GREY_400
                                ),
                            ],
                            spacing=2,
                            expand=True
                        ),
                        ft.Text(
                            applicant.submitted_at.strftime("%H:%M:%S"),
                            size=11,
                            color=ft.Colors.GREY_500
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
            )
        )

        # Green success toast
        page.show_dialog(
            ft.SnackBar(
                content=ft.Text(f"Application accepted for {clean_name}!"),
                bgcolor=ft.Colors.GREEN_700,
                behavior=ft.SnackBarBehavior.FLOATING
            )
        )

        # Reset the form
        name_field.value = ""
        id_field.value = ""
        email_field.value = ""
        phone_field.value = ""
        gwa_field.value = ""
        program_dropdown.value = None

        # Update the counter text
        status_summary.value = f"Applications registered this session: {len(approved_applicants)}"

        page.update()

    # Layout Assembly
    submit_button = ft.FilledButton(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE),
                ft.Text("Submit Scholarship Application", weight=ft.FontWeight.BOLD)
            ],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.BLUE_700,
            shape=ft.RoundedRectangleBorder(radius=8)
        ),
        height=48,
        width=float("inf"),
        on_click=submit_application
    )

    page.add(
        ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.LOCAL_POLICE, size=32, color=ft.Colors.BLUE_400),
                        ft.Column(
                            controls=[
                                ft.Text("CSPC Scholarship Intake Portal", size=20, weight=ft.FontWeight.BOLD),
                                ft.Text("Office of Student Affairs & Services • Academic Year 2026–2027", size=12, color=ft.Colors.GREY_400)
                            ],
                            spacing=2
                        )
                    ]
                ),
                ft.Divider(height=20, color=ft.Colors.OUTLINE_VARIANT),
                name_field,
                id_field,
                email_field,
                phone_field,
                gwa_field,
                program_dropdown,
                ft.Container(height=10),
                submit_button,
                ft.Container(height=5),
                status_summary,
                ft.Divider(height=20, color=ft.Colors.OUTLINE_VARIANT),
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.HISTORY, size=16),
                        ft.Text(
                            "Recent Session Intake Contracts (In-Memory Pre-Persistence)",
                            size=13,
                            weight=ft.FontWeight.BOLD
                        ),
                    ]
                ),
            
                ft.Container(height=20),  # bottom breathing room so the last card isn't cramped
            ],
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
    )


if __name__ == "__main__":
    ft.run(main)
