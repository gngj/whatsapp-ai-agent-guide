# 04 – Voice notes: download and transcribe

## What arrives

A voice note reaches your webhook as a message of type `audio` and **contains no audio**. It only contains a media id:

```json
{
  "from": "<SENDER_E164_DIGITS>",
  "id": "wamid.<...>",
  "timestamp": "<UNIX_SECONDS>",
  "type": "audio",
  "audio": {
    "id": "<MEDIA_ID>",
    "mime_type": "audio/ogg; codecs=opus",
    "sha256": "<BASE64_SHA256>",
    "url": "https://lookaside.fbsbx.com/whatsapp_business/attachments/?mid=…",
    "voice": true
  }
}
```

- `voice: true` means it was recorded in WhatsApp as a voice message. An uploaded audio file has `voice` false or absent.
- The `url` in the webhook (when present) is **useless without your token** and expires within minutes.
- A media id from a webhook can be downloaded for **7 days**.

The same flow works for `image`, `document`, `video` and `sticker` messages. Only the field name changes.

## Download: two authenticated GETs

**1. Resolve the media id to a fresh URL:**

```bash
curl -s "https://graph.facebook.com/v23.0/<MEDIA_ID>?phone_number_id=<PHONE_NUMBER_ID>" \
  -H "Authorization: Bearer $WHATSAPP_TOKEN"
```

```json
{ "messaging_product": "whatsapp", "url": "https://lookaside.fbsbx.com/…", "mime_type": "audio/ogg",
  "sha256": "<HEX_SHA256>", "file_size": "<BYTES>", "id": "<MEDIA_ID>" }
```

`phone_number_id` is optional. If you include it, the call succeeds only when the media belongs to that number.

**2. Download the file with the same Bearer header**, within about **5 minutes**:

```bash
curl -s "<URL_FROM_STEP_1>" -H "Authorization: Bearer $WHATSAPP_TOKEN" -o voice.ogg
```

Without the header the request fails. If you get `404`, the URL has expired, so repeat step 1. If it still fails, check the token.

Good practice, all of which the example script does:

- Send the Bearer header only to Meta hosts (`graph.facebook.com`, `lookaside.fbsbx.com`, `*.fbcdn.net`, `*.whatsapp.net`). Don't follow redirects to anywhere else with the token attached.
- Check the downloaded bytes against `sha256` from step 1 (hex).
- Cap the size. Cloud API media can be up to 100 MB, and audio messages are at most 16 MB.
- Generate your own file name. Never build a path from webhook data.
- Have the download tool return only the **local path, MIME type and size** to the agent. Return neither the token nor the signed URL.

## Transcribe locally: ffmpeg + faster-whisper

WhatsApp voice notes are Ogg/Opus. Convert them to 16 kHz mono WAV and run [faster-whisper](https://github.com/SYSTRAN/faster-whisper), a fast CTranslate2 implementation of OpenAI Whisper that runs on CPU:

```bash
# one-time setup
sudo apt-get install -y ffmpeg          # macOS: brew install ffmpeg
python3 -m venv .venv && .venv/bin/pip install faster-whisper

# per voice note
ffmpeg -hide_banner -loglevel error -y -i voice.ogg -ac 1 -ar 16000 voice.wav
.venv/bin/python - <<'PY'
from faster_whisper import WhisperModel
model = WhisperModel("large-v3", device="cpu", compute_type="int8")
segments, info = model.transcribe("voice.wav", vad_filter=True, beam_size=5)  # add language="he" etc. to force a language
print(info.language, "".join(s.text for s in segments).strip())
PY
```

Choosing a model:

| Model | Download | Quality | CPU speed |
| --- | --- | --- | --- |
| `small` | ~0.5 GB | OK for clear English | fast |
| `medium` | ~1.5 GB | good | moderate |
| `large-v3` | ~3 GB | best, especially for non-English languages | slow on CPU (around real time or slower), fine for short notes |

Tips:

- **Set `language=`** when you know it. Auto-detection on short clips sometimes guesses wrong.
- `vad_filter=True` skips silence and reduces hallucinated text at the end.
- The first run downloads the model, so cache it (`HF_HOME` / `download_root`).
- Expect small transcription errors in names and slang. Have the agent restate what it understood before acting on a voice instruction.
- With a GPU, use `device="cuda", compute_type="float16"`.

## All-in-one script

[`../examples/transcribe_voice_note.py`](../examples/transcribe_voice_note.py) takes a media id and does both GETs, the host allowlist, the SHA-256 check, ffmpeg and faster-whisper. It reads the token from a file path in an environment variable, so the token is never in argv, the environment, or the output:

```bash
export WHATSAPP_ACCESS_TOKEN_FILE=~/.secrets/whatsapp_token   # chmod 600
export WHATSAPP_PHONE_NUMBER_ID=<PHONE_NUMBER_ID>               # optional
python examples/transcribe_voice_note.py <MEDIA_ID> --language en --model large-v3
# → JSON: {"audio_path": "...", "mime_type": "audio/ogg", "size": 101124, "language": "en", "transcript": "..."}
```

An agent then needs only one tool, "transcribe this media id", and it never handles the token.

Next: [05 – Testing & troubleshooting](05-testing-troubleshooting.md).
