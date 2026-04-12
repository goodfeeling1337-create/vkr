from io import BytesIO

import openpyxl
from openpyxl import load_workbook

from app.checker.common.workbook_validator import WorkbookValidator


def test_rejects_multi_sheet() -> None:
    wb = openpyxl.Workbook()
    wb.create_sheet("Second")
    v = WorkbookValidator().validate(wb)
    assert not v.ok


def test_accepts_single_sheet_with_sections(sample_workbook_bytes: bytes) -> None:
    wb = load_workbook(BytesIO(sample_workbook_bytes), data_only=True)
    v = WorkbookValidator().validate(wb)
    assert v.ok
    assert v.sheet_name == "Лист1"
