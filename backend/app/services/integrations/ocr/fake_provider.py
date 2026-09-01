"""Synthetic Fake OCR Provider for Development & Testing."""

from typing import Any

from app.services.integrations.ocr.base import OcrProvider


class FakeOcrProvider(OcrProvider):
    """Synthetic OCR provider returning mock extracted fields with confidence ratings."""

    def __init__(self, fail_mode: bool = False):
        self.fail_mode = fail_mode

    async def extract_text(self, document_url: str) -> str:
        if self.fail_mode:
            raise RuntimeError("OCR Engine processing failure")
        return (
            "CHIEF RED BEAR CHILDREN'S LODGE INTAKE REFERRAL FORM\n"
            "Client Name: Jordan Bear\n"
            "Date of Birth: 2014-05-12\n"
            "Healthcare Number: 9948201948\n"
            "Allegation: Educational neglect noted by school counselor."
        )

    async def extract_fields(self, document_url: str) -> dict[str, Any]:
        if self.fail_mode:
            raise RuntimeError("OCR Engine processing failure")
        return {
            "candidate_fields": [
                {
                    "field_name": "first_name",
                    "value": "Jordan",
                    "confidence": 0.95,
                    "target_domain": "client.identifiers",
                },
                {
                    "field_name": "last_name",
                    "value": "Bear",
                    "confidence": 0.94,
                    "target_domain": "client.identifiers",
                },
                {
                    "field_name": "date_of_birth",
                    "value": "2014-05-12",
                    "confidence": 0.89,
                    "target_domain": "client.identifiers",
                },
                {
                    "field_name": "health_card_number",
                    "value": "9948201948",
                    "confidence": 0.92,
                    "target_domain": "client.identifiers",
                },
            ]
        }

    async def health_check(self) -> dict[str, Any]:
        if self.fail_mode:
            return {"status": "ERROR", "message": "OCR Engine offline"}
        return {"status": "OK", "provider": "FakeOcrProvider"}
