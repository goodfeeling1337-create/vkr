from __future__ import annotations

from dataclasses import dataclass

from openpyxl.workbook.workbook import Workbook

from app.checker.common.section_locator import SectionLocator


@dataclass
class WorkbookValidationResult:
    ok: bool
    errors: list[str]
    sheet_name: str | None = None


class WorkbookValidator:
    """Validates structural constraints for .xlsx homework files."""

    def validate(self, wb: Workbook) -> WorkbookValidationResult:
        errors: list[str] = []
        if wb is None:
            return WorkbookValidationResult(False, ["Файл не загружен"], None)
        names = wb.sheetnames
        if len(names) != 1:
            errors.append(f"Ожидается один лист, найдено: {len(names)}")
            return WorkbookValidationResult(False, errors, None)
        ws = wb[names[0]]
        matrix: list[list[object]] = []
        for row in ws.iter_rows(values_only=True):
            matrix.append(list(row))
        loc = SectionLocator(matrix)
        hits = loc.find_sections()
        for n in range(1, 14):
            if n not in hits:
                errors.append(f'Не найдена секция "Задание №{n}"')
        ok = len(errors) == 0
        return WorkbookValidationResult(ok, errors, names[0])
