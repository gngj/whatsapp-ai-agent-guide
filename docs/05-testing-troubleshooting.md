# 05 – Testing & troubleshooting

## End-to-end checklist

Work through these in order. Each step isolates one layer.

1. **Endpoint handshake works locally.**
   ```bash
   curl -i "http://127.0.0.1:8787/?hub.mode=subscribe&hub.verify_token=$VERIFY_TOKEN&hub.challenge=abc123"   # → 200, body "abc123"
   curl -i "http://127.0.0.1:8787/?hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=abc123"          # → 403
   ```
2. **Handshake works through the public URL.** Repeat (1) against `https://<YOUR_PUBLIC_HOST>/…`.
3. **Meta accepts the URL.** Dashboard → Configuration → Webhook → *Verify and save* succeeds.
4. **`messages` field is subscribed.** It shows *Subscribed* under Webhook fields.
5. **Dashboard test reaches you.** Click **Test** next to `messages`. A sample payload ("this is a text message", fake numbers) shows up in your logs.
6. **App is Live.** Without this, step 7 fails silently. See [01 → Step 12](01-meta-setup.md#step-12-publish-the-app-live-mode).
7. **A real message reaches you.** Send "hi" from your verified phone to the business number. A POST with `value.messages[0].text.body == "hi"` arrives.
8. **Outbound works.** Send free text back (the window is open because of step 7). Check that the webhook then receives `statuses` events: `sent`, `delivered`, `read`.
9. **Template works outside the window.** Send `hello_world` or your own template.
10. **Voice note works.** Record a short voice note, take `audio.id` from the webhook, and run the transcription script.

## Symptoms and fixes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| *Verify and save* fails: "The callback URL or verify token couldn't be validated" | Endpoint unreachable, not HTTPS or self-signed, returns JSON or quotes instead of the bare challenge, or token mismatch (watch for trailing whitespace/newline) | Test with `curl` from outside your network. Return `text/plain` with exactly the challenge |
| Verified, but nothing ever arrives | `messages` field not subscribed | Subscribe under Webhook fields |
| Dashboard **Test** arrives, real phone messages don't | App is **unpublished** (dev mode delivers only dashboard tests) | Add a privacy policy URL and publish (01 → Step 12) |
| Still nothing after publishing | App isn't subscribed to the WABA, or the webhook belongs to a different app than the number's WABA | `GET /<WABA_ID>/subscribed_apps`. `POST` to subscribe if empty |
| Only an `account_update` / `WEBHOOK_CONFIG_UPDATED` event arrived | That's a subscription-change notice. It confirms connectivity, not message delivery | Check the `messages` subscription and the items above |
| Events stop after hours or days | Tunnel restarted with a new URL, or the free tunnel dropped | Use a static domain, a relay, or serverless. Otherwise re-enter the Callback URL after every restart |
| Same message processed twice | Meta retried because you didn't answer 200 fast enough | Return 200 immediately and dedupe on `messages[].id` |
| Send returns 200 but nothing arrives on the phone | Failure only shows up in `statuses[].errors` (e.g. 131047 outside the window) | Log status webhooks and use a template |
| `131030` recipient not allowed | Test number can only message verified recipients | Add the number under API Setup → To → Manage |
| `190` after a day | You're still using the temporary token | Switch to the system-user token |
| `200` / "does not have permission" with the system-user token | System user isn't assigned the **exact** WABA that owns the number, or has only partial access | Business Settings → System users → Assign assets → the right WhatsApp account with full control |
| Portfolio creation: "account too new" | New Facebook account | Wait about an hour (sometimes a few hours) and retry |
| Name rejected (portfolio, app, or system user) | Too generic, or contains a trademark such as "WhatsApp" | Use a more specific name without Meta trademarks |
| Generated token, then can't see it again | Meta shows tokens only once | Generate a new token and store it immediately |
| Media download `401`/`403` | Missing Bearer header on the second GET, or token lacks access to that number | Send the header on both GETs and check the WABA assignment |
| Media download `404` | Signed URL expired (about 5 min) | Call `GET /<MEDIA_ID>` again, then download right away |
| Transcript in the wrong language or garbled | Auto-detect on a short clip, or model too small | Pass `language=` and use `large-v3` |

## Useful diagnostics

```bash
# What phone numbers does this WABA have, and what are their IDs and status?
curl -s "https://graph.facebook.com/v23.0/<WABA_ID>/phone_numbers?fields=id,display_phone_number,verified_name,quality_rating,status" \
  -H "Authorization: Bearer $WHATSAPP_TOKEN"

# Is the token valid, which type, which scopes, when does it expire?
curl -s "https://graph.facebook.com/v23.0/debug_token?input_token=$WHATSAPP_TOKEN" \
  -H "Authorization: Bearer $WHATSAPP_TOKEN" | jq '.data | {type, is_valid, expires_at, scopes}'

# Which apps are subscribed to this WABA's webhooks?
curl -s "https://graph.facebook.com/v23.0/<WABA_ID>/subscribed_apps" -H "Authorization: Bearer $WHATSAPP_TOKEN"
```

Also useful: **App Dashboard → Webhooks → Recent deliveries/errors** (when shown), **WhatsApp Manager → Insights**, and Meta's [API status page](https://metastatus.com/whatsapp-business-api).

> When pasting logs into an issue or a chat, strip the `Authorization` header, signed media URLs, the verify token, and the app secret first. Phone numbers in payloads are personal data too.
