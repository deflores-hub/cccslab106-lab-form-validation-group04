import re
from dataclasses import dataclass
import flet as ft

# ==========================================
# TIER 1: CUSTOM DOMAIN EXCEPTION HIERARCHY
# ==========================================

class ScholarshipValidationError(Exception):
    """Base exception class for all scholarship validation errors."""
    pass

class IDFormatError(ScholarshipValidationError):
    """Raised when student ID does not match the 20XX-XXXX(X) pattern."""
    pass

class EmailDomainError(ScholarshipValidationError):
    """Raised when email does not belong to @cspc.edu.ph domain."""
    pass

class GWARangeError(ScholarshipValidationError):
    """Raised when GWA is non-numeric or outside the 1.00 - 5.00 range."""
    pass


# ==========================================
# PRE-COMPILED REGULAR EXPRESSIONS
# ==========================================

STUDENT_ID_REGEX = re.compile(r"^20\d{2}-\d{4,5}$")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@cspc\.edu\.ph$")
PHONE_REGEX = re.compile(r"^(?:\+63|0)9\d{9}$")


# ==========================================
# TIER 2: DOMAIN VALIDATOR ENGINE
# ==========================================

class ScholarshipValidator:
    """Static validation logic for all scholarship application fields."""

    @staticmethod
    def validate_name(name: str) -> str:
        clean_name = name.strip() if name else ""
        if not clean_name or len(clean_name) < 2:
            raise ScholarshipValidationError("Full name must be at least 2 characters long.")
        if any(char.isdigit() for char in clean_name):
            raise ScholarshipValidationError("Full name cannot contain numeric digits.")
        if "<" in clean_name or ">" in clean_name:
            raise ScholarshipValidationError("Full name cannot contain HTML tags or angle brackets.")
        return clean_name

    @staticmethod
    def validate_student_id(student_id: str) -> str:
        clean_id = student_id.strip() if student_id else ""
        if not STUDENT_ID_REGEX.match(clean_id):
            raise IDFormatError("Student ID must follow format 20XX-XXXX or 20XX-XXXXX (e.g., 2024-0123).")
        return clean_id

    @staticmethod
    def validate_email(email: str) -> str:
        clean_email = email.strip().lower() if email else ""
        if not EMAIL_REGEX.match(clean_email):
            raise EmailDomainError("Must use a valid institutional email ending with @cspc.edu.ph.")
        return clean_email

    @staticmethod
    def validate_phone(phone: str) -> str:
        raw_phone = phone.strip() if phone else ""
        cleaned = re.sub(r"[\s\-]", "", raw_phone)
        
        if cleaned.startswith("+63"):
            cleaned = "0" + cleaned[3:]
            
        if not re.match(r"^09\d{9}$", cleaned):
            raise ScholarshipValidationError("Phone number must be a valid PH mobile number starting with 09 (11 digits).")
        return cleaned

    @staticmethod
    def validate_gwa(gwa_str: str) -> float:
        clean_gwa = gwa_str.strip() if gwa_str else ""
        try:
            val = float(clean_gwa)
        except (ValueError, TypeError):
            raise GWARangeError("GWA must be a valid numeric decimal (e.g., 1.45).")
            
        if not (1.00 <= val <= 5.00):
            raise GWARangeError("GWA must be between 1.00 (Highest) and 5.00 (Failing).")
        return val


# ==========================================
# TIER 4: IMMUTABLE DOMAIN DATA CONTRACT
# ==========================================

@dataclass(frozen=True)
class ScholarshipApplicant:
    full_name: str
    student_id: str
    email: str
    phone: str
    gwa: float
    program: str


# ==========================================
# TIER 3: FLET GUI & EVENT HANDLERS
# ==========================================

def main(page: ft.Page):
    page.title = "CSPC Scholarship Application Portal"
    page.window.width = 600
    page.window.height = 800
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # Form Controls
    name_field = ft.TextField(label="Full Name", hint_text="e.g. Maria Clara Santos")
    id_field = ft.TextField(label="Student ID Number", hint_text="e.g. 2024-0891")
    email_field = ft.TextField(label="Institutional Email", hint_text="e.g. mclara.santos@cspc.edu.ph")
    phone_field = ft.TextField(label="Mobile Number", hint_text="e.g. 09181234567 or +63 918-123-4567")
    gwa_field = ft.TextField(label="General Weighted Average (GWA)", hint_text="e.g. 1.45")
    
    program_dropdown = ft.Dropdown(
        label="Scholarship Program",
        options=[
            ft.dropdown.Option("DOST Science & Technology Scholarship"),
            ft.dropdown.Option("CHED Tulong Dunong Program"),
            ft.dropdown.Option("CSPC Academic Honor Support"),
        ],
    )

    cards_column = ft.Column()

    # Reactive error clearing on typing/changing inputs
    def clear_error(e):
        e.control.error_text = None
        page.update()

    name_field.on_change = clear_error
    id_field.on_change = clear_error
    email_field.on_change = clear_error
    phone_field.on_change = clear_error
    gwa_field.on_change = clear_error
    program_dropdown.on_change = clear_error

    def clear_all_errors():
        name_field.error_text = None
        id_field.error_text = None
        email_field.error_text = None
        phone_field.error_text = None
        gwa_field.error_text = None
        program_dropdown.error_text = None

    def submit_application(e):
        clear_all_errors()
        has_error = False

        # Validate Full Name
        try:
            valid_name = ScholarshipValidator.validate_name(name_field.value)
        except ScholarshipValidationError as err:
            name_field.error_text = str(err)
            has_error = True

        # Validate Student ID
        try:
            valid_id = ScholarshipValidator.validate_student_id(id_field.value)
        except IDFormatError as err:
            id_field.error_text = str(err)
            has_error = True

        # Validate Institutional Email
        try:
            valid_email = ScholarshipValidator.validate_email(email_field.value)
        except EmailDomainError as err:
            email_field.error_text = str(err)
            has_error = True

        # Validate Mobile Phone
        try:
            valid_phone = ScholarshipValidator.validate_phone(phone_field.value)
        except ScholarshipValidationError as err:
            phone_field.error_text = str(err)
            has_error = True

        # Validate GWA
        try:
            valid_gwa = ScholarshipValidator.validate_gwa(gwa_field.value)
        except GWARangeError as err:
            gwa_field.error_text = str(err)
            has_error = True

        # Validate Program Selection
        if not program_dropdown.value:
            program_dropdown.error_text = "Please select a scholarship program."
            has_error = True

        if has_error:
            page.show_dialog(
                ft.SnackBar(content=ft.Text("Validation failed. Please correct highlighted errors."), bg_color=ft.Colors.RED_700)
            )
            page.update()
            return

        # If all valid, instantiate immutable dataclass contract
        applicant = ScholarshipApplicant(
            full_name=valid_name,
            student_id=valid_id,
            email=valid_email,
            phone=valid_phone,
            gwa=valid_gwa,
            program=program_dropdown.value,
        )

        # Build application summary card
        card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Application Received", weight=ft.FontWeight.BOLD, size=16),
                    ft.Text(f"Applicant: {applicant.full_name}"),
                    ft.Text(f"ID: {applicant.student_id} | Email: {applicant.email}"),
                    ft.Text(f"Phone: {applicant.phone} | GWA: {applicant.gwa:.2f}"),
                    ft.Text(f"Program: {applicant.program}"),
                ]),
                padding=15,
                border=ft.Border.all(1, ft.Colors.GREEN_400),
                border_radius=8,
            )
        )
        cards_column.controls.insert(0, card)

        # Show success notification & reset inputs
        page.show_dialog(
            ft.SnackBar(content=ft.Text("Application submitted successfully!"), bg_color=ft.Colors.GREEN_700)
        )
        name_field.value = ""
        id_field.value = ""
        email_field.value = ""
        phone_field.value = ""
        gwa_field.value = ""
        program_dropdown.value = None
        
        page.update()

    submit_btn = ft.FilledButton("Submit Application", on_click=submit_application)

    main_container = ft.Column([
        ft.Text("CSPC Scholarship Portal", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
        ft.Divider(),
        name_field,
        id_field,
        email_field,
        phone_field,
        gwa_field,
        program_dropdown,
        ft.Container(height=10),
        submit_btn,
        ft.Divider(),
        ft.Text("Submitted Applications", style=ft.TextThemeStyle.TITLE_MEDIUM),
        cards_column,
    ])

    page.add(main_container)

if __name__ == "__main__":
    ft.app(target=main)