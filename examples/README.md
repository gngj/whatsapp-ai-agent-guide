# Examples

| File | What it does |
| --- | --- |
| `webhook_server.py` | Minimal webhook (standard library only). Answers the `hub.challenge` handshake, checks `X-Hub-Signature-256` when you give it an app secret, deduplicates, and appends messages and statuses to `events.jsonl`. Never logs query strings. |
| `transcribe_voice_note.py` | Takes a media id and does `GET /{media-id}`, then an authenticated download, a SHA-256 check, `ffmpeg` and `faster-whisper`, and prints JSON with the path and transcript. Reads the token from a file and never prints it. |

```bash
# webhook (put a tunnel or TLS proxy in front of port 8787)
export VERIFY_TOKEN_FILE=~/.secrets/wa_verify_token APP_SECRET_FILE=~/.secrets/wa_app_secret
python3 examples/webhook_server.py

# voice note
python3 -m venv .venv && .venv/bin/pip install faster-whisper
export WHATSAPP_ACCESS_TOKEN_FILE=~/.secrets/wa_token
.venv/bin/python examples/transcribe_voice_note.py <MEDIA_ID> --language en
```

Create secret files with `umask 077` (or `chmod 600` afterwards) and keep them out of the repository.
