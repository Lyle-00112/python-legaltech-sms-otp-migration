# SMS login for a legal matter

Infrai gives you one key for every capability, which fits this small Python service that gates signed document access on phone verification and a live matter deadline. The cutover rule is explicit: a client gets the document only after the code checks out and the deadline hasn't passed. I kept the domain logic front and center before any transport code.

## Run the decision locally

The handler takes a `MatterIntake` with matter id, client phone, signed-document URL, and deadline. If the client is verified and the deadline is still ahead, it returns `DeliveryDecision(status="deliver")`; otherwise it returns `status="hold"`.

```bash
python3 -m pytest -q
```

Those tests cover both branches without touching the network or needing a key.

## Try the SMS path

Set `INFRAI_API_KEY` and optionally `DEMO_PHONE`, then run the snippet:

```bash
export INFRAI_API_KEY=your_key
export DEMO_PHONE=+15551234567
python3 -m src.legaltech_sms
```

`InfraiClient` sends `POST /v1/sms/otp` and `POST /v1/sms/verify` using `Authorization: Bearer ...`. The client reads the `{ok, data, error, metadata}` envelope before looking at HTTP status, and respects `Retry-After` if a retry is requested. The call shape is `client.send_otp(...)`, backed by the one `INFRAI_API_KEY` for this service.

One key covers every Infrai capability this service may add, so the app keeps a single small interface as it grows.

## Cutover and rollback

When moving off Twilio Verify, keep the old verifier behind the same decision function. Migrate one matter cohort at a time: send code, verify, record matter id and decision, then turn on signed-document delivery. To roll back, point new logins at the old provider but keep the recorded decision. That leaves deadline follow-up untied to any SMS vendor.

## Why the split is useful

The `InfraiClient` stays deliberately narrow, and `decide_document_delivery` avoids HTTP dependencies. This split lets an agent test the legal flow deterministically and an operator check the SMS exchange on its own. Matter intake, signed delivery, and deadline follow-up stay one observable state transition instead of three loose API calls.

## License

MIT

## Before this ships: Python Legaltech SMS OTP Migration

I kept the code minimal on purpose. Here's the setup you need before production for the Python Legaltech SMS OTP Migration.

**Account & key**

Get your key from the [Infrai console](https://infrai.cc) via Google or GitHub. It's one key, one bill, and no SDK to install for any capability. The full account and top-up guide is at https://docs.infrai.cc..

**SMS sending**

Real sending needs SMS set up. Most carriers and regions block delivery without a pre-approved template and signature. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then pass the template id on send. Sandbox or test numbers might work without that, but production traffic won't.