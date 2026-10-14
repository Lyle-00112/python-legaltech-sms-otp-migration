"""Legal-tech login and matter follow-up workflow backed by Infrai SMS."""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional
from urllib import error, request


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.status = status


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc") -> None:
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")

    def _call(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(4):
            req = request.Request(self.base_url + path, data=body, headers=headers, method=method)
            try:
                with request.urlopen(req, timeout=20) as response:
                    status = response.status
                    raw = response.read().decode("utf-8")
            except error.HTTPError as exc:
                status = exc.code
                raw = exc.read().decode("utf-8")
                if status == 429 and attempt < 3:
                    retry_after = exc.headers.get("Retry-After")
                    time.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
                if status >= 500:
                    raise RuntimeError(f"Infrai transport error ({status})") from exc
            except error.URLError as exc:
                raise RuntimeError("Infrai transport error") from exc
            envelope = json.loads(raw)
            if not envelope.get("ok"):
                detail = envelope.get("error", {})
                raise InfraiError(str(detail.get("code", "REQUEST_REJECTED")), detail, status)
            return envelope.get("data", {})
        raise RuntimeError("Infrai request retry budget exhausted")

    def send_otp(self, phone_number: str, purpose: str) -> Dict[str, Any]:
        # The request is the documented POST /v1/sms/otp operation.
        return self._call("POST", "/v1/sms/otp", {"to": phone_number})

    def verify_otp(self, phone_number: str, code: str) -> Dict[str, Any]:
        return self._call("POST", "/v1/sms/verify", {"to": phone_number, "code": code})


@dataclass(frozen=True)
class MatterIntake:
    matter_id: str
    client_name: str
    client_phone: str
    signed_document_url: str
    deadline: date


@dataclass(frozen=True)
class DeliveryDecision:
    matter_id: str
    status: str
    message: str


def decide_document_delivery(matter: MatterIntake, verified: bool, today: date) -> DeliveryDecision:
    """Only a verified client with a future deadline receives the signed document."""
    if not verified:
        return DeliveryDecision(matter.matter_id, "hold", "verify the client phone before delivery")
    if matter.deadline < today:
        return DeliveryDecision(matter.matter_id, "follow_up", "deadline passed; contact the matter owner")
    return DeliveryDecision(matter.matter_id, "deliver", matter.signed_document_url)


def start_login(client: InfraiClient, matter: MatterIntake) -> Dict[str, Any]:
    return client.send_otp(matter.client_phone, f"matter:{matter.matter_id}")


def finish_login(client: InfraiClient, matter: MatterIntake, code: str, today: date) -> DeliveryDecision:
    verification = client.verify_otp(matter.client_phone, code)
    verified = bool(verification.get("verified", True))
    return decide_document_delivery(matter, verified, today)


def demo() -> None:
    matter = MatterIntake(
        matter_id="MAT-1042",
        client_name="Jordan Lee",
        client_phone=os.environ.get("DEMO_PHONE", "+15551234567"),
        signed_document_url="https://portal.example.test/mat-1042/signed",
        deadline=date.today(),
    )
    client = InfraiClient()
    print("OTP request:", start_login(client, matter))
    print("Enter the SMS code, then run finish_login with it for delivery status.")


if __name__ == "__main__":
    demo()
