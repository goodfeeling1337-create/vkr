from app.checker.error_catalog import NormalizationErrorCatalog


def test_catalog_has_core_codes():
    codes = {e.code for e in NormalizationErrorCatalog.all_errors()}
    assert "FD_MISSING" in codes
    assert "PK_WRONG" in codes
    assert "PK_INCOMPLETE" in codes
    assert "PK_REDUNDANT" in codes
    assert "PK_NON_UNIQUE_ON_ROWS" in codes
    assert "SCHEMA_EXTRA_RELATIONS" in codes


def test_for_task_filters():
    fd_codes = {e.code for e in NormalizationErrorCatalog.for_task(6)}
    assert "PARTIAL_AS_FULL" in fd_codes
