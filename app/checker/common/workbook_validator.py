from __future__ import annotations

from dataclasses import dataclass

from openpyxl.workbook.workbook import Workbook

from app.checker.common.section_locator import SectionLocator

META_SHEET_NAME = "__template_meta__"


def data_sheet_names(wb: Workbook) -> list[str]:
    """Имена листов с ответами (без служебного листа метаданных шаблона)."""
    return [n for n in wb.sheetnames if n != META_SHEET_NAME]


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
        names = data_sheet_names(wb)
        if len(names) != 1:
            extra = len(wb.sheetnames) - len(names)
            if extra and len(names) == 0:
                errors.append("В книге только служебные листы; нужен лист с заданиями")
            else:
                errors.append(
                    f"Ожидается один лист с ответами (плюс опционально «{META_SHEET_NAME}»), "
                    f"листов с заданиями: {len(names)}",
                )
            return WorkbookValidationResult(False, errors, None)
        sheet_name = names[0]
        ws = wb[sheet_name]
        matrix: list[list[object]] = []
        for row in ws.iter_rows(values_only=True):
            matrix.append(list(row))
        loc = SectionLocator(matrix)
        hits = loc.find_sections()
        for n in range(1, 14):
            if n not in hits:
                errors.append(f'Не найдена секция «Задание №{n}»')
        ok = len(errors) == 0
        return WorkbookValidationResult(ok, errors, sheet_name)
