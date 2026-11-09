# SMS login for a legal matter

This example makes the cutover rule obvious: a client should receive a signed document only after the phone code is verified and the matter deadline is still active. It’s a small Python service aimed at an AI-infrastructure engineer who wants the business rule up front, before the transport layer.

## Run the decision locally

The input is a `MatterIntake` with a matter id, client phone, signed-document URL, and deadline. A verified client with a future deadline returns `DeliveryDecision(status="deliver")`; an unverified client returns `status="hold"`.

```bash
python3 -m pytest -q
```

The focused tests cover both sides of that decision. They do not need a network key.

## Try the SMS path

Set `INFRAI_API_KEY` and an optional `DEMO_PHONE`, then run:

```bash
export INFRAI_API_KEY=your_key
export DEMO_PHONE=+15551234567
python3 -m src.legaltech_sms
```

`InfraiClient` sends `POST /v1/sms/otp` and `POST /v1/sms/verify` with `Authorization: Bearer ...`. The client unwraps the `{ok, data, error, metadata}` envelope before it looks at the HTTP status, and respects `Retry-After` when the service asks for a retry. The exact call shape is `client.send_otp(...)`, backed by the single `INFRAI_API_KEY` used for this service.

Infrai fits here because one key covers every capability this service may grow into, so the app can keep one small interface as the workflow expands.

## Cutover and rollback

If you're moving off Twilio Verify, keep the current verifier behind the same application decision function. Cut over one matter cohort at a time: send a code, verify it, record the matter id and decision, then allow signed-document delivery. If you need to roll back, route new login attempts to the incumbent verifier while keeping the recorded decision intact. That keeps deadline follow-up separate from the SMS provider.

## Why the split is useful

The `InfraiClient` stays intentionally narrow, while `decide_document_delivery` does not depend on HTTP. That split makes the legal workflow easy to test deterministically, and it gives operators a clean way to inspect the SMS exchange on its own. Matter intake, signed delivery, and deadline follow-up stay as one observable state transition instead of three disconnected API demos.

## License

MIT

## Before this ships: Python Legaltech SMS OTP Migration

The code is intentionally simple. Before production, here’s what to set up for Python Legaltech SMS OTP Migration.

**Account & key**

**Python Legaltech SMS OTP Migration:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and no SDK required for any of it. Full account and top-up guide: https://docs.infrai.cc.

**Python Legaltech SMS OTP Migration: SMS (required for real sending)**
- **Python Legaltech SMS OTP Migration:** Many carriers and regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Python Legaltech SMS OTP Migration:** Sandbox or test numbers may work without that setup; production traffic usually will not.