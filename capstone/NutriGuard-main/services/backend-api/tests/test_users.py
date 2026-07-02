from types import SimpleNamespace

from app.routes.users import (
    SUPPLEMENT_ALIASES,
    TERM_ALIASES,
    hash_password,
    merge_unique,
    normalize_goals,
    normalize_terms,
    verify_password,
)


def test_normalize_terms_detects_aliases_and_short_explicit_terms():
    result = normalize_terms(
        "Low ferritin, vitamin d, custom need, this phrase is too long to keep",
        TERM_ALIASES,
    )

    assert "iron_deficiency" in result
    assert "vitamin_d_deficiency" in result
    assert "custom_need" in result
    assert "this_phrase_is_too_long_to_keep" not in result


def test_normalize_terms_for_supplements_uses_canonical_names():
    result = normalize_terms("I take ferrous tablets and methylcobalamin", SUPPLEMENT_ALIASES)

    assert result == ["iron_tablet", "vitamin_b12"]


def test_merge_unique_preserves_order_and_removes_duplicates():
    assert merge_unique(["iron_deficiency"], ["iron_deficiency", "diabetes"], None) == [
        "iron_deficiency",
        "diabetes",
    ]


def test_normalize_goals_supports_multiple_goals_and_default():
    payload = SimpleNamespace(goal="muscle_gain", goals=["fat_loss", "muscle_gain"])
    assert normalize_goals(payload) == ["muscle_gain", "fat_loss"]

    empty_payload = SimpleNamespace(goal=None, goals=None)
    assert normalize_goals(empty_payload) == ["maintenance"]


def test_password_hash_round_trip_and_rejects_bad_values():
    stored_hash = hash_password("Admin123")

    assert verify_password("Admin123", stored_hash) is True
    assert verify_password("Wrong123", stored_hash) is False
    assert verify_password("Admin123", None) is False
    assert verify_password("Admin123", "not-a-valid-hash") is False
