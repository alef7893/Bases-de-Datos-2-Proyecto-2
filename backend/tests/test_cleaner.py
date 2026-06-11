from src.multimodal.stage_01_content.cleaner import (
    build_canonical_text,
    clean_html,
    flatten_attribute_values,
    normalize_value,
)


def test_clean_html_and_normalize_values() -> None:
    assert clean_html("<p>Machine <strong>wash</strong><br>cold</p>") == (
        "Machine wash cold"
    )
    assert normalize_value(" NA ") == ""


def test_build_canonical_text_and_attributes() -> None:
    attributes = flatten_attribute_values({"Pattern": "Printed", "Empty": None})

    assert attributes == ["Pattern", "Printed", "Empty"]
    assert build_canonical_text(["  Black ", "", "sports   shoes"]) == (
        "Black sports shoes"
    )



