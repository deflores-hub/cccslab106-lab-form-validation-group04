"""
CCCS 106: Application Development and Emerging Technologies
Week 5 Laboratory Task: CSPC Scholarship Intake Portal (Real-time PubSub Enabled)
Instructor: Allan O. Ibo, Jr., MSc
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import flet as ft


# ============================================================================
# TIER 3: DOMAIN DATA CONTRACT & CUSTOM EXCEPTIONS
# ============================================================================

class ScholarshipValidationError(Exception):
    pass

class IDFormatError(ScholarshipValidationError):
    pass

class EmailDomainError(ScholarshipValidationError):
    pass

class GWARangeError(ScholarshipValidationError):
    pass


@dataclass(frozen=True)
class ScholarshipApplicant:
    full_name: str
    student_id: str
    email: str
    phone: str
    gwa: float
    program: str
    submitted_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# TIER 2: VALIDATION ENGINE
# ============================================================================

class ScholarshipValidator:
    NAME_REGEX = re.compile(r"^[A-Za-z\s.\-',]{2,60}$")
    STUDENT_ID_REGEX = re.compile(r"^20\d{2}-\d{4,5}$")
    CSPC_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@cspc\.edu\.ph$")
    PH_PHONE_REGEX = re.compile(r"^(?:\+63|0)9\d{9}$")

    @classmethod
    def sanitize_string(cls, raw: Optional[str]) -> str:
        return (raw or "").strip()

    @classmethod
    def validate_name(cls, value: Optional[str]) -> str:
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
            raise IDFormatError("Invalid Student ID format. Use format YYYY-NNNN (e.g., 2024-0123).")
        return clean

    @classmethod
    def validate_email(cls, value: Optional[str]) -> str:
        clean = cls.sanitize_string(value).lower()
        if not clean:
            raise EmailDomainError("Institutional email is required.")
        if not cls.CSPC_EMAIL_REGEX.match(clean):
            raise EmailDomainError("Must use a valid institutional email (@cspc.edu.ph).")
        return clean

    @classmethod
    def validate_phone(cls, value: Optional[str]) -> str:
        clean = cls.sanitize_string(value)
        cleaned = re.sub(r"[\s\-]", "", clean)
        if not cls.PH_PHONE_REGEX.match(cleaned):
            raise ScholarshipValidationError("Enter a valid PH mobile number (e.g., 09181234567 or +639181234567).")
        if cleaned.startswith("+63"):
            cleaned = "0" + cleaned[3:]
        return cleaned

    @classmethod
    def validate_gwa(cls, value: Optional[str]) -> float:
        clean = cls.sanitize_string(value)
        if not clean:
            raise GWARangeError("GWA is required.")
        try:
            gwa_val = float(clean)
        except ValueError:
            raise GWARangeError("GWA must be a numeric decimal value.")
        if not (1.00 <= gwa_val <= 5.00):
            raise GWARangeError("GWA must be between 1.00 and 5.00.")
        return gwa_val


# Shared in-memory list across all active browser connections
GLOBAL_APPLICANTS = []

def main(page: ft.Page):
    page.title = "CSPC Scholarship Intake Portal"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 25

    recent_contracts_column = ft.Column(spacing=10)

    # UI Controls
    name_field = ft.TextField(label="Full Name", hint_text="e.g., Maria Clara Santos", prefix_icon=ft.Icons.PERSON_OUTLINE, border_radius=8)
    id_field = ft.TextField(label="Student ID Number", hint_text="e.g., 2024-0123", prefix_icon=ft.Icons.BADGE_OUTLINED, border_radius=8)
    email_field = ft.TextField(label="Institutional Email", hint_text="e.g., mclara.santos@cspc.edu.ph", prefix_icon=ft.Icons.ALTERNATE_EMAIL, border_radius=8)
    phone_field = ft.TextField(label="Philippine Mobile Number", hint_text="e.g., 09181234567", prefix_icon=ft.Icons.PHONE_ANDROID_OUTLINED, border_radius=8)
    gwa_field = ft.TextField(label="Academic General Weighted Average (GWA)", hint_text="Scale: 1.00 to 5.00", prefix_icon=ft.Icons.GRADE_OUTLINED, border_radius=8)

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

    status_summary = ft.Text(value=f"Applications registered this session: {len(GLOBAL_APPLICANTS)}", color=ft.Colors.GREY_400, size=13)

    def show_toast(message: str, bg_color: str):
        snack = ft.SnackBar(content=ft.Text(message), bgcolor=bg_color, behavior=ft.SnackBarBehavior.FLOATING)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def clear_field_error(e):
        if hasattr(e.control, 'error') and e.control.error:
            e.control.error = None
            page.update()
        elif hasattr(e.control, 'error_text') and e.control.error_text:
            e.control.error_text = None
            page.update()

    def clear_dropdown_error(e):
        if e.control.error_text:
            e.control.error_text = None
            page.update()

    name_field.on_change = clear_field_error
    id_field.on_change = clear_field_error
    email_field.on_change = clear_field_error
    phone_field.on_change = clear_field_error
    gwa_field.on_change = clear_field_error
    program_dropdown.on_change = clear_dropdown_error

    def set_field_error(field_control, err_msg: str):
        if hasattr(field_control, 'error'):
            field_control.error = err_msg
        else:
            field_control.error_text = err_msg

    def render_card(applicant_dict):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_400, size=24),
                    ft.Column(
                        controls=[
                            ft.Text(f"{applicant_dict['name']} ({applicant_dict['id']})", weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.WHITE),
                            ft.Text(f"{applicant_dict['program']} • GWA: {applicant_dict['gwa']} • {applicant_dict['email']}", size=12, color=ft.Colors.GREY_400),
                        ],
                        spacing=2,
                        expand=True
                    ),
                    ft.Text(applicant_dict['timestamp'], size=12, color=ft.Colors.GREY_500)
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=12,
            bgcolor="#24262b",
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
        )

    # Load existing cards on page load
    for item in reversed(GLOBAL_APPLICANTS):
        recent_contracts_column.controls.append(render_card(item))

    # Real-time Broadcast Listener
    def on_broadcast(data):
        recent_contracts_column.controls.insert(0, render_card(data))
        status_summary.value = f"Applications registered this session: {len(GLOBAL_APPLICANTS)}"
        page.update()

    page.pubsub.subscribe(on_broadcast)

    def submit_application(e):
        has_errors = False
        name_field.error = None
        id_field.error = None
        email_field.error = None
        phone_field.error = None
        gwa_field.error = None
        program_dropdown.error_text = None

        try:
            clean_name = ScholarshipValidator.validate_name(name_field.value)
        except ScholarshipValidationError as err:
            set_field_error(name_field, str(err))
            has_errors = True

        try:
            clean_id = ScholarshipValidator.validate_student_id(id_field.value)
        except IDFormatError as err:
            set_field_error(id_field, str(err))
            has_errors = True

        try:
            clean_email = ScholarshipValidator.validate_email(email_field.value)
        except EmailDomainError as err:
            set_field_error(email_field, str(err))
            has_errors = True

        try:
            clean_phone = ScholarshipValidator.validate_phone(phone_field.value)
        except ScholarshipValidationError as err:
            set_field_error(phone_field, str(err))
            has_errors = True

        try:
            clean_gwa = ScholarshipValidator.validate_gwa(gwa_field.value)
        except GWARangeError as err:
            set_field_error(gwa_field, str(err))
            has_errors = True

        if not program_dropdown.value:
            program_dropdown.error_text = "Please select a scholarship program."
            has_errors = True

        if has_errors:
            show_toast("Validation failed: Please correct highlighted fields.", ft.Colors.RED_700)
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        record_data = {
            "name": clean_name,
            "id": clean_id,
            "email": clean_email,
            "program": program_dropdown.value,
            "gwa": f"{clean_gwa:.2f}",
            "timestamp": timestamp
        }

        GLOBAL_APPLICANTS.append(record_data)

        # Broadcast to all connected clients instantly
        page.pubsub.send_all(record_data)

        name_field.value = ""
        id_field.value = ""
        email_field.value = ""
        phone_field.value = ""
        gwa_field.value = ""
        program_dropdown.value = None

        show_toast(f"Application accepted for {clean_name}", ft.Colors.GREEN_700)

    submit_button = ft.FilledButton(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE),
                ft.Text("Submit Scholarship Application", weight=ft.FontWeight.BOLD)
            ],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, shape=ft.RoundedRectangleBorder(radius=8)),
        height=48,
        on_click=submit_application
    )

    page.add(
        ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.SHIELD_OUTLINED, size=32, color=ft.Colors.BLUE_400),
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
                ft.Container(height=5),
                submit_button,
                ft.Container(height=5),
                status_summary,
                ft.Divider(height=20, color=ft.Colors.OUTLINE_VARIANT),
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.HISTORY, size=16, color=ft.Colors.GREY_400),
                        ft.Text("Recent Session Intake Contracts (In-Memory Pre-Persistence)", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_300)
                    ]
                ),
                recent_contracts_column
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO
        )
    )
if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8550)