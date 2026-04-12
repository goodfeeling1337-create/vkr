from io import BytesIO

import openpyxl
from openpyxl import load_workbook

from app.checker.common.workbook_validator import WorkbookValidator


def test_rejects_multi_sheet() -> None:
    wb = openpyxl.Workbook()
    wb.create_sheet("Second")
    v = WorkbookValidator().validate(wb)
    assert not v.ok


def test_accepts_answer_sheet_plus_template_meta_sheet() -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Лист1"
    row = 1
    for n in range(1, 14):
        ws.cell(row=row, column=2, value=f"Задание №{n}")
        row += 1
    wb.create_sheet("__template_meta__")
    v = WorkbookValidator().validate(wb)
    assert v.ok
    assert v.sheet_name == "Лист1"


def test_accepts_single_sheet_with_sections(sample_workbook_bytes: bytes) -> None:
    wb = load_workbook(BytesIO(sample_workbook_bytes), data_only=True)
    v = WorkbookValidator().validate(wb)
    assert v.ok
    assert v.sheet_name == "Лист1"
