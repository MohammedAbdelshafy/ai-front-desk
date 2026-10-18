from pathlib import Path

from ai_front_desk.clinical.avatar_customizer import AVATAR_ASSETS, render_avatar_customizer


BASE = Path(__file__).resolve().parents[1] / "ai_front_desk" / "clinical"


def test_shared_avatar_customizer_is_safe_local_first_and_reusable():
    html = render_avatar_customizer("Personalize OB-GYN Mia")
    assert "Personalize OB-GYN Mia" in html
    assert 'data-mia-avatar-widget' in html
    assert 'data-mia-avatar-preset="clinician-f"' in html
    assert 'data-mia-avatar-upload' in html
    assert 'data-mia-avatar-export' in html
    assert 'data-mia-avatar-import' in html
    assert "not uploaded or sent to an AI service" in html
    assert "/assets/mia-avatar.js" in html
    assert "/assets/mia-avatar.css" in html


def test_avatar_assets_exist_and_have_expected_content_types():
    assert set(AVATAR_ASSETS) == {"mia-avatar.js", "mia-avatar.css"}
    for name, (content_type, filename) in AVATAR_ASSETS.items():
        path = BASE / "static" / filename
        assert path.exists()
        assert path.is_file()
        assert path.stat().st_size > 100
        assert content_type.startswith("text/")
    js = (BASE / "static" / "mia-avatar.js").read_text(encoding="utf-8")
    assert "localStorage" in js
    assert "MAX_UPLOAD_BYTES" in js
    assert "URL.createObjectURL" in js
    assert "FormData" not in js
    assert "fetch(" not in js


def test_dental_medication_workbench_has_personalizable_avatar():
    from ai_front_desk.clinical.medication_workbench import render_page

    page = render_page()
    assert "Change avatar" in page
    assert 'data-mia-avatar-shell' in page
    assert 'data-default-src="/assets/mia-stand-hi.webp"' in page
    assert 'data-mia-avatar-upload' in page


def test_obgyn_workbench_has_separate_specialty_and_avatar_widget():
    from ai_front_desk.clinical.obgyn_workbench import render_page

    page = render_page()
    assert "OB-GYN Clinical Reference Workbench" in page
    assert "Personalize your OB-GYN Mia" in page
    assert "data-mia-avatar-widget" in page
    assert "obstetrics and gynaecology" in page
    assert "SYNTHETIC CASES ONLY" in page


def test_main_mia_intake_pages_share_avatar_customizer():
    from ai_front_desk.clinical.server import render_landing

    page = render_landing()
    assert "Personalize your Mia" in page
    assert "data-mia-avatar-shell" in page
    assert "data-mia-avatar-widget" in page
