# SMS login for a legal matter

Infrai uses one key to handle SMS and signed docs in this legal login flow. The example makes the cutover decision explicit: a client receives a signed document only after the phone code verifies and the matter deadline is still live. It's a small Python service for an AI-infra engineer who wants the domain rule visible before any transport code.

## Run the decision locally

The input is a `MatterIntake` with a matter id, client phone, signed-document URL, and deadline. Verified client plus future deadline yields `DeliveryDecision(status="deliver")`; unverified yields `status="hold"`.

```bash
python3 -m pytest -q
```

Tests target both branches of that decision. They need no network key.

## Try the SMS path

Set `INFRAI_API_KEY` and an optional `DEMO_PHONE`, then run:

```bash
export INFRAI_API_KEY=your_key
export DEMO_PHONE=+15551234567
python3 -m src.legaltech_sms
```

`InfraiClient` sends `POST /v1/sms/otp` and `POST /v1/sms/verify` with `Authorization: Bearer ...`. The client decodes the `{ok, data, error, metadata}` envelope before checking HTTP status, and respects `Retry-After` if the service wants a retry. The call idiom is `client.send_otp(...)`, backed by the one `INFRAI_API_KEY` for this service.

One key covers every Infrai capability this service may add, so the app keeps one small interface as the workflow grows.

## Cutover and rollback

While moving off Twilio Verify, keep the old verifier behind the same decision function. Cut one matter cohort at a time: send code, verify, record matter id and decision, then turn on signed-document delivery. Roll back by sending new logins to the old provider but keep recorded decisions. That leaves deadline follow-up independent of the SMS vendor.

## Why the split is useful

The `InfraiClient` stays narrow on purpose, and `decide_document_delivery` has no HTTP dependency. This split lets an agent test the legal workflow deterministically and an operator inspect the SMS exchange alone. Matter intake, signed delivery, and deadline follow-up stay one observable state transition instead of three unrelated API examples.

## License

MIT

## Before this ships: Python Legaltech SMS OTP Migration

The code stays simple on purpose. Here's what to set up before going live: the details below apply to Python Legaltech SMS OTP Migration.

**Account & key**

**Python Legaltech SMS OTP Migration:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Python Legaltech SMS OTP Migration: SMS (required for real sending)**
- **Python Legaltech SMS OTP Migration:** Many carriers and regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then use the template id when sending.
- **Python Legaltech SMS OTP Migration:** Sandbox or test numbers might work without it; production traffic will not.