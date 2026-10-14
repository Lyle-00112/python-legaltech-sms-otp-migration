from datetime import date

from src.legaltech_sms import MatterIntake, decide_document_delivery


def test_verified_client_with_live_deadline_receives_signed_document():
    matter = MatterIntake("MAT-1", "Ari", "+15550000000", "https://portal.test/signed", date(2026, 10, 1))
    decision = decide_document_delivery(matter, verified=True, today=date(2026, 9, 9))
    assert decision.status == "deliver"
    assert decision.message == matter.signed_document_url


def test_unverified_client_is_held_even_when_deadline_is_live():
    matter = MatterIntake("MAT-2", "Ari", "+15550000000", "https://portal.test/signed", date(2026, 10, 1))
    assert decide_document_delivery(matter, verified=False, today=date(2026, 9, 9)).status == "hold"
