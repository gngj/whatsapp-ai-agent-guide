# 03 – Outbound: sending messages

Every send is a POST to the phone number's `messages` edge:

```
POST https://graph.facebook.com/v23.0/<PHONE_NUMBER_ID>/messages
Authorization: Bearer <SYSTEM_USER_TOKEN>
Content-Type: application/json
```

`to` is the recipient in E.164 **digits only**: country code and number, no `+`, spaces or leading zero. For example, the UK number `07700 900123` becomes `447700900123`.

## The 24-hour customer service window

| Situation | What you can send |
| --- | --- |
| The user messaged you in the last 24 hours | **Free-form** messages: text, media, reactions, interactive buttons/lists |
| No message from the user in 24 hours (or ever) | **Only an approved template** |

The window opens (or resets) every time **the user** sends you a message. Your own messages don't extend it. For an agent that sends proactive notifications, plan on templates, or ask the user to message the number from time to time.

## Free-form text

```bash
curl -s "https://graph.facebook.com/v23.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer $WHATSAPP_TOKEN" -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "recipient_type": "individual",
    "to": "<RECIPIENT_E164_DIGITS>",
    "type": "text",
    "text": { "body": "Your report is ready.", "preview_url": false }
  }'
```

Replying to a specific message (shows a quote bubble): add `"context": {"message_id": "wamid.<...>"}`.

Mark an inbound message as read (blue ticks) and optionally show a typing indicator while your agent thinks:

```bash
curl -s "https://graph.facebook.com/v23.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer $WHATSAPP_TOKEN" -H "Content-Type: application/json" \
  -d '{"messaging_product":"whatsapp","status":"read","message_id":"wamid.<...>","typing_indicator":{"type":"text"}}'
```

## Templates

The test account comes with `hello_world` (language `en_US`). Create your own templates in **WhatsApp Manager → Message templates** or with `POST /<WABA_ID>/message_templates`. Meta reviews every template, usually within minutes. Categories are **Utility** (transactional notices), **Marketing**, and **Authentication**. A notification-style agent usually needs a Utility template with one variable:

```bash
curl -s "https://graph.facebook.com/v23.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer $WHATSAPP_TOKEN" -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "to": "<RECIPIENT_E164_DIGITS>",
    "type": "template",
    "template": {
      "name": "<TEMPLATE_NAME>",
      "language": { "code": "<LANG_CODE>" },
      "components": [{ "type": "body", "parameters": [{ "type": "text", "text": "Build finished" }] }]
    }
  }'
```

List templates and their review status:

```bash
curl -s "https://graph.facebook.com/v23.0/<WABA_ID>/message_templates?fields=name,status,category,language" \
  -H "Authorization: Bearer $WHATSAPP_TOKEN"
```

## Reading the response

A `200` with `{"messages":[{"id":"wamid..."}]}` means **accepted, not delivered**. The actual outcome arrives later on your webhook as a `statuses[]` entry (`sent` → `delivered` → `read`, or `failed` with an error code). Always log and check those statuses. A failure caused by the 24-hour window, for example, often shows up **only** there.

## Common errors

| Code | Meaning | Fix |
| --- | --- | --- |
| `190` | Token invalid or expired | Temporary tokens expire in <24 h. Use the system-user token (01 → Step 10) |
| `200` / `10` | Permission error, e.g. the app or system user can't access this WABA or number | Assign the **exact** WABA that owns `<PHONE_NUMBER_ID>` to the system user with full control, then regenerate the token if scopes are missing |
| `100` | Invalid parameter | Check JSON shape, `messaging_product`, the `to` format, and template `components` |
| `131030` | Recipient not in allowed list | With the test number, add and verify the recipient (01 → Step 5) |
| `131047` | Re-engagement required: more than 24 h since the user's last message | Send a template, or wait for the user to write |
| `131026` | Message undeliverable | Recipient has no WhatsApp, has an old app, or hasn't accepted terms. Check the number |
| `131021` | Sender and recipient are the same number | Use a different phone for testing |
| `132000` / `132001` | Template parameter count mismatch / template doesn't exist in that language | Match the variable count and use the exact `name` and `language.code` |
| `132015` / `132016` | Template paused or disabled for low quality | Edit the template or create a new one |
| `131056` / `130429` / `80007` | Rate limits (pair rate, throughput, WABA) | Back off and retry. Don't spam one recipient |
| `131009` | Parameter value not valid, for example an expired media id | Re-upload media or fix the value |
| `133010` | Phone number not registered | Register the number (`POST /<PHONE_NUMBER_ID>/register`). Real numbers only |

The full list is in Meta's [error codes reference](https://developers.facebook.com/documentation/business-messaging/whatsapp/support/error-codes).

Next: [04 – Voice notes](04-voice-notes.md).
