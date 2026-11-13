#!/usr/bin/env python3
"""Download a WhatsApp Cloud API media item by media id and transcribe it.

    python transcribe_voice_note.py <MEDIA_ID> [--language en] [--model large-v3] [--out-dir ./media] [--no-transcribe]

Environment:
  WHATSAPP_ACCESS_TOKEN_FILE  path to a chmod-600 file with the system-user token (required)
  WHATSAPP_PHONE_NUMBER_ID    optional; restricts the lookup to media of this number
  GRAPH_API_VERSION           default v23.0

Prints one JSON object: audio_path, mime_type, size, language, transcript.
The token is read inside this process and is never printed, logged, put in argv, or put in the environment.
The signed download URL is never printed either.

Requires: Python 3.10+, ffmpeg on PATH, `pip install faster-whisper` (only for transcription).
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ALLOWED_HOSTS = ("graph.facebook.com", "lookaside.fbsbx.com")
ALLOWED_SUFFIXES = (".fbcdn.net", ".whatsapp.net", ".fbsbx.com")
MAX_BYTES = 100 * 1024 * 1024
EXT = {"audio/ogg": "ogg", "audio/opus": "ogg", "audio/mpeg": "mp3", "audio/mp4": "m4a",
       "audio/aac": "aac", "audio/amr": "amr", "image/jpeg": "jpg", "image/png": "png",
       "image/webp": "webp", "video/mp4": "mp4", "application/pdf": "pdf"}


def fail(msg: str, code: int = 1) -> None:
    print(json.dumps({"error": msg}), file=sys.stderr)
    sys.exit(code)


def load_token() -> str:
    path = os.environ.get("WHATSAPP_ACCESS_TOKEN_FILE")
    if not path or not Path(path).is_file():
        fail("set WHATSAPP_ACCESS_TOKEN_FILE to a readable token file")
    token = Path(path).read_text().strip()
    if not token:
        fail("token file is empty")
    return token


def check_host(url: str) -> None:
    u = urllib.parse.urlparse(url)
    host = (u.hostname or "").lower()
    if u.scheme != "https" or not (host in ALLOWED_HOSTS or host.endswith(ALLOWED_SUFFIXES)):
        fail(f"refusing to send the token to {host or 'an invalid URL'}")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # we follow redirects ourselves, after checking the host
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def authed_get(url: str, token: str, max_redirects: int = 5) -> tuple[bytes, str]:
    for _ in range(max_redirects + 1):
        check_host(url)
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "User-Agent": "wa-media-fetch/1.0"})
        try:
            with OPENER.open(req, timeout=60) as resp:
                data = resp.read(MAX_BYTES + 1)
                if len(data) > MAX_BYTES:
                    fail("media larger than limit")
                return data, (resp.headers.get("Content-Type") or "application/octet-stream")
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308) and e.headers.get("Location"):
                url = urllib.parse.urljoin(url, e.headers["Location"])
                continue
            detail = e.read(500).decode("utf-8", "replace").replace(token, "[redacted]")
            fail(f"HTTP {e.code} from {urllib.parse.urlparse(url).hostname}: {detail}")
        except urllib.error.URLError as e:
            fail(f"network error: {e.reason}")
    fail("too many redirects")
    raise AssertionError  # unreachable


def sha_matches(data: bytes, expected: str) -> bool:
    expected = expected.strip()
    digest = hashlib.sha256(data).digest()
    if re.fullmatch(r"[0-9a-fA-F]{64}", expected):
        return digest.hex() == expected.lower()
    try:
        return base64.b64decode(expected) == digest
    except ValueError:
        return False


def download(media_id: str, out_dir: Path) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9._-]+", media_id) or ".." in media_id:
        fail("invalid media id", 2)
    token = load_token()
    version = os.environ.get("GRAPH_API_VERSION", "v23.0")
    query = {}
    if os.environ.get("WHATSAPP_PHONE_NUMBER_ID"):
        query["phone_number_id"] = os.environ["WHATSAPP_PHONE_NUMBER_ID"]
    meta_url = f"https://graph.facebook.com/{version}/{media_id}"
    if query:
        meta_url += "?" + urllib.parse.urlencode(query)

    raw, _ = authed_get(meta_url, token)           # step 1: media id -> short-lived URL
    meta = json.loads(raw)
    if "url" not in meta:
        fail("Graph response had no download url")
    data, ctype = authed_get(meta["url"], token)   # step 2: download with the same Bearer header
    del token

    if meta.get("sha256") and not sha_matches(data, meta["sha256"]):
        fail("sha256 mismatch")
    mime = (meta.get("mime_type") or ctype).split(";")[0].strip().lower()
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "_", media_id)[:80]
    path = out_dir / f"wa-{safe_id}-{secrets.token_hex(4)}.{EXT.get(mime, 'bin')}"
    with open(path, "xb") as f:
        f.write(data)
    return {"audio_path": str(path), "mime_type": mime, "size": len(data)}


def transcribe(path: Path, model_name: str, language: str | None) -> tuple[str, str]:
    wav = path.with_suffix(".wav")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(path), "-ac", "1", "-ar", "16000", str(wav)], check=True)
    from faster_whisper import WhisperModel  # imported lazily so --no-transcribe works without it

    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(wav), language=language, vad_filter=True, beam_size=5)
    text = "".join(s.text for s in segments).strip()
    return info.language, text


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("media_id")
    p.add_argument("--out-dir", default="media")
    p.add_argument("--model", default="large-v3", help="faster-whisper model: small, medium, large-v3, ...")
    p.add_argument("--language", default=None, help="ISO code such as en, he, es; omit to auto-detect")
    p.add_argument("--no-transcribe", action="store_true")
    a = p.parse_args()

    result = download(a.media_id, Path(a.out_dir))
    if not a.no_transcribe:
        lang, text = transcribe(Path(result["audio_path"]), a.model, a.language)
        result.update(language=lang, transcript=text)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
