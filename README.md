# Connect an AI agent to WhatsApp (WhatsApp Cloud API): Quick start

This guide shows how to give an AI agent its own WhatsApp number using Meta's **official WhatsApp Cloud API**. When you're done, the agent can:

- **receive** WhatsApp messages (text, voice notes, images, documents) through a webhook,
- **send** replies and notifications (free text inside the 24-hour window, approved templates outside it),
- **transcribe voice notes** locally with `ffmpeg` and `faster-whisper`.

It uses only Meta's official API. No WhatsApp Web automation or unofficial clients are involved. To get started you only need Meta's free test number.

> The full guide lives in [`docs/`](docs/). This page is the one-page version.

## What you need

- A Facebook account. A brand-new account works, but Meta may make you **wait about an hour** before it lets you create a business portfolio.
- A phone with WhatsApp to send and receive test messages. It must be a different number from the business number.
- A public **HTTPS** URL for the webhook: a hosted webhook relay, a serverless function, or a tunnel to your machine.
- `curl`. For voice notes you also need Python 3.10+, `ffmpeg` and `faster-whisper`.

## The 10 steps

1. **Facebook account.** Create one, or use an existing one. Verify it by email.
2. **Meta developer.** At [developers.facebook.com](https://developers.facebook.com), click **Get started** and verify a mobile number by SMS.
3. **App.** Go to **My Apps → Create App**, pick the **Connect with customers through WhatsApp** use case, and create a business portfolio or pick one you already have. If Meta says the account is too new, wait about an hour and try again.
4. **Test number.** Open **Use cases → Customize → API Setup** (also labeled *WhatsApp → API Setup*). Meta gives you a free test number. Copy the **Phone number ID** and the **WhatsApp Business Account ID** (newer pages call it the *Messaging account ID*).
5. **Recipients.** In the **To** field, add your own WhatsApp number and enter the code WhatsApp sends you. A test number can message up to 5 verified recipients.
6. **First message.** Click **Generate access token** and then **Send message**. The `hello_world` template should arrive on your phone. **Reply to it.** Your reply opens the 24-hour window.
7. **Permanent token.** In **Business Settings → Users → System users**, add a system user. **Assign assets**: the app and the *exact* WhatsApp account that holds your test number, both with full control. Then **Generate token** with `whatsapp_business_messaging` and `whatsapp_business_management`, and set it to never expire. Store it in a secrets manager or a `chmod 600` file. Never paste it into chats, logs or the repo.
8. **Webhook.** Stand up an HTTPS endpoint that answers Meta's `hub.challenge` GET and accepts POSTs (see [`examples/webhook_server.py`](examples/webhook_server.py)). In **Configuration → Webhook**, enter the **Callback URL** and a **Verify token** you made up, click **Verify and save**, and then **subscribe to the `messages` field**.
9. **Publish the app.** In development mode Meta delivers only the dashboard's *Test* webhooks, not real messages. Add a **Privacy Policy URL** under **App settings → Basic** and switch the app to **Live** (**Publish**).
10. **Test end to end.** Send a WhatsApp message to the test number. It should reach your webhook, and your agent can reply:

```bash
curl "https://graph.facebook.com/v23.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer $WHATSAPP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"messaging_product":"whatsapp","to":"<RECIPIENT_E164_DIGITS>","type":"text","text":{"body":"Hello from my agent"}}'
```

## Voice notes in one paragraph

The webhook doesn't contain the audio. It only contains `audio.id`. Call `GET /<MEDIA_ID>` with your token to get a short-lived `url`, which is valid for about 5 minutes. Then `GET` that url **with the same Bearer header** to download the `.ogg`/opus file. Convert it with `ffmpeg` to 16 kHz mono WAV and transcribe it with `faster-whisper`. [`examples/transcribe_voice_note.py`](examples/transcribe_voice_note.py) does all of this, and the token never leaves the process.

## Full guide

| Doc | Covers |
| --- | --- |
| [01 – Meta setup, step by step](docs/01-meta-setup.md) | Facebook account, developer registration, app, test number, business portfolio, system user, permanent token, webhook config, publishing |
| [02 – Inbound webhook](docs/02-inbound-webhook.md) | Verification handshake, payloads, hosting options (relay, serverless, tunnel) with pros and cons |
| [03 – Outbound messages](docs/03-outbound.md) | `/messages` endpoint, the 24-hour window and templates, common errors |
| [04 – Voice notes](docs/04-voice-notes.md) | Media download flow and local transcription |
| [05 – Testing & troubleshooting](docs/05-testing-troubleshooting.md) | End-to-end checklist and the problems people actually hit |

Placeholders like `<PHONE_NUMBER_ID>`, `<WABA_ID>` and `<RECIPIENT_E164_DIGITS>` stand for your own values. API examples use Graph API `v23.0`. Any current version works, and [Meta's changelog](https://developers.facebook.com/docs/graph-api/changelog) lists the latest one.
