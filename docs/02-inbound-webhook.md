# 02 – Inbound: the webhook

WhatsApp Cloud API has **no inbox you can poll**. Every inbound message reaches you as an HTTPS POST from Meta to a URL you register. Meta also keeps no history you can fetch later, so if your endpoint is down, you only get Meta's retries (see below).

## What the endpoint must do

1. **GET (verification).** When you click *Verify and save*, Meta calls:

   ```
   GET <CALLBACK_URL>?hub.mode=subscribe&hub.verify_token=<VERIFY_TOKEN>&hub.challenge=<RANDOM>
   ```

   If `hub.mode == "subscribe"` and the token matches yours, reply **HTTP 200 with the raw `hub.challenge` value as the body** (plain text, nothing else). Otherwise reply 403.

2. **POST (events).** Meta sends JSON with header `X-Hub-Signature-256: sha256=<hmac>`. Reply **200 quickly**. Do the slow work (LLM calls, transcription) asynchronously. If you don't return 200, Meta retries immediately and then with decreasing frequency for up to 7 days, so **deduplicate on the message `id`**.

3. **Validate (recommended).** Compute HMAC-SHA256 of the raw body using your **app secret** and compare it to the header.

Requirements: a valid public TLS certificate (self-signed certificates are rejected), port 443, and a URL that stays stable. If the URL changes, you have to re-enter it in the dashboard.

A complete minimal server is in [`../examples/webhook_server.py`](../examples/webhook_server.py) (standard library only).

## What a message payload looks like

```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "id": "<WABA_ID>",
    "changes": [{
      "field": "messages",
      "value": {
        "messaging_product": "whatsapp",
        "metadata": { "display_phone_number": "<BUSINESS_NUMBER>", "phone_number_id": "<PHONE_NUMBER_ID>" },
        "contacts": [{ "profile": { "name": "<SENDER_NAME>" }, "wa_id": "<SENDER_E164_DIGITS>" }],
        "messages": [{
          "from": "<SENDER_E164_DIGITS>",
          "id": "wamid.<...>",
          "timestamp": "<UNIX_SECONDS>",
          "type": "text",
          "text": { "body": "Hi!" }
        }]
      }
    }]
  }]
}
```

Things to handle:

- `value.messages[]`: inbound messages. `type` is `text`, `audio`, `image`, `document`, `video`, `sticker`, `location`, `reaction`, `interactive`, `button`, and so on. Media types carry an `id` (see [04 – Voice notes](04-voice-notes.md)). Voice notes have `"type": "audio"` and `"audio": {"voice": true, ...}`.
- `value.statuses[]`: delivery receipts for *your* outbound messages (`sent`, `delivered`, `read`, `failed` with an `errors[]` array). They arrive on the same `messages` field, so don't treat them as user messages.
- Other fields (`account_update`, `message_template_status_update`, …) arrive only if you subscribe to them. You may see an `account_update` with event `WEBHOOK_CONFIG_UPDATED` when an app's subscription to the WABA changes. That is a configuration notice, not a message.
- The sender may also carry a business-scoped user id (`user_id` / `from_user_id`). Store it alongside the phone number if you see it.
- Use `timestamp` (seconds since epoch, UTC) for ordering. Don't use arrival time.

## Hosting options

Meta needs a public HTTPS URL. Your agent usually runs somewhere that isn't publicly reachable (a laptop, a sandbox VM, a desktop app). There are three common ways to bridge that gap:

### A. Hosted webhook relay / listener service

A third-party service gives you a stable HTTPS URL, answers the verification handshake for you, stores the incoming events, and forwards them to your agent. It can do that by waking it, pushing to a queue, calling another webhook, or offering an API or MCP tool to read them. Many agent platforms, automation tools (Make, n8n, Zapier-style), and generic webhook inbox services offer this.

| Pros | Cons |
| --- | --- |
| Stable URL, no server to run | Message content passes through a third party, so read their privacy terms |
| Handles verification, retries, buffering while your agent is offline | Another account, and possibly another cost |
| Usually has a log or UI to see what arrived | Limited control over payload handling. Generic content filters may mis-flag Meta's long numeric IDs |
| Often supports signature validation with your app secret | You depend on their uptime |

### B. Serverless function

Deploy a small function (Cloudflare Workers, Vercel/Netlify functions, AWS Lambda + Function URL, Google Cloud Run/Functions, Azure Functions) that verifies the handshake, validates the signature, and writes events to a store your agent reads: a queue, KV, a database, or a push to the agent.

| Pros | Cons |
| --- | --- |
| Stable HTTPS URL with real TLS | You write and maintain the code |
| Free tiers cover personal volumes | You need a place to store events and a way to notify the agent |
| Data stays in an account you control | Cold starts. Keep the handler fast and return 200 before slow work |
| Easy to add signature checks and dedup | |

### C. Tunnel to a local server

Run the webhook server on the agent's machine and expose it with a tunnel (Cloudflare Tunnel, ngrok, Tailscale Funnel, localhost.run, and similar).

| Pros | Cons |
| --- | --- |
| Fastest way to see real payloads | **Free tunnels often give a new random URL on every restart.** You must re-enter the Callback URL in Meta each time, and you lose messages while it's down |
| Everything runs locally, so your agent reads events directly | Free tiers drop idle connections, which means you need a keep-alive/restart loop |
| No cloud account needed for quick tests | Machine must stay on; corporate proxies may break the tunnel client (e.g. certificate revocation checks) |

A tunnel with a **reserved/static domain** (paid ngrok, Cloudflare named tunnel on your own domain) removes most of these problems.

### Which one?

- **Quick experiment:** tunnel (C).
- **Personal agent you rely on daily:** hosted relay (A) if your agent platform has one, otherwise serverless (B).
- **Anything with other people's messages:** serverless (B) or your own server, with signature validation and a clear data-retention policy.

## Overriding the callback per WABA or number (advanced)

The dashboard callback is per **app**. If you need different endpoints per WhatsApp account or phone number, Meta supports **callback URL overrides** through `POST /<WABA_ID>/subscribed_apps` (with `override_callback_uri` and `verify_token`) and on the phone number. You also use `GET /<WABA_ID>/subscribed_apps` to check that your app is subscribed to the WABA at all:

```bash
curl -s "https://graph.facebook.com/v23.0/<WABA_ID>/subscribed_apps" -H "Authorization: Bearer $WHATSAPP_TOKEN"
# Subscribe if the list is empty:
curl -s -X POST "https://graph.facebook.com/v23.0/<WABA_ID>/subscribed_apps" -H "Authorization: Bearer $WHATSAPP_TOKEN"
```

Next: [03 – Outbound](03-outbound.md).
