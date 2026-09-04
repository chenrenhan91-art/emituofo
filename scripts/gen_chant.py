#!/usr/bin/env python3
"""Pre-render sutra verses with macOS Tingting, pausing like the original system TTS."""
import json
import re
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "index.html"
OUT = ROOT / "audio"
VERSES_JSON = ROOT / "audio/verses.json"
VOICE = "Tingting"
# Close to the app default speechSynthesis rate 0.85 (“缓”)
SAY_RATE = 175

# Match speakTTS waits: 。！？ 320ms, ； 200ms, others 140ms
PAUSE = {
    "，": 0.14,
    "、": 0.14,
    "：": 0.14,
    "；": 0.20,
    "。": 0.32,
    "！": 0.32,
    "？": 0.32,
}


def extract_verses(html: str):
    start = html.index("const SUTRA_DATABASE")
    end = html.index("const ACHIEVEMENTS")
    block = html[start:end]
    items = []
    for m in re.finditer(
        r'id: "(?P<id>[^"]+)"[\s\S]*?verses: \[(?P<verses>[\s\S]*?)\]\s*\}',
        block,
    ):
        texts = re.findall(r'text: "((?:\\.|[^"\\])*)"', m.group("verses"))
        items.append({"id": m.group("id"), "verses": texts})
    return items


def split_clauses(text: str):
    chunks = []
    buf = ""
    for ch in text:
        buf += ch
        if ch in PAUSE:
            part = buf.strip()
            if part:
                chunks.append((part, PAUSE[ch]))
            buf = ""
    if buf.strip():
        chunks.append((buf.strip(), 0.14))
    return chunks or [(text, 0.14)]


def concat_wav(parts, dest: Path):
    frames = []
    params = None
    for i, (path, gap) in enumerate(parts):
        with wave.open(str(path), "rb") as w:
            if params is None:
                params = w.getparams()
            frames.append(w.readframes(w.getnframes()))
        if i < len(parts) - 1 and gap > 0:
            frames.append(b"\x00\x00" * int(params.framerate * gap))
    dest.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(dest), "wb") as w:
        w.setparams(params)
        w.writeframes(b"".join(frames))


def say_wav(text: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    aiff = dest.with_suffix(".aiff")
    proc = subprocess.run(
        ["say", "-v", VOICE, "-r", str(SAY_RATE), "-o", str(aiff), text],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0 or not aiff.exists() or aiff.stat().st_size < 400:
        raise RuntimeError(f"say failed for {dest}: {(proc.stderr or '')[-400:]}")
    conv = subprocess.run(
        ["afconvert", "-f", "WAVE", "-d", "LEI16@22050", str(aiff), str(dest)],
        capture_output=True,
        text=True,
    )
    aiff.unlink(missing_ok=True)
    if conv.returncode != 0 or not dest.exists() or dest.stat().st_size < 800:
        raise RuntimeError(f"afconvert wav failed for {dest}: {conv.stderr[-400:]}")


def to_m4a(wav: Path, m4a: Path):
    subprocess.run(
        ["afconvert", "-f", "m4af", "-d", "aac", "-b", "64000", str(wav), str(m4a)],
        check=True,
        capture_output=True,
    )


def synth_verse(sid, stem, text, tmp):
    clauses = split_clauses(text)
    wav_parts = []
    for j, (clause, gap) in enumerate(clauses):
        part = tmp / f"{sid}-{stem}-{j}.wav"
        print(f"synth {sid}/{stem} [{j + 1}/{len(clauses)}] {clause[:24]}")
        say_wav(clause, part)
        wav_parts.append((part, gap))
    wav = tmp / f"{sid}-{stem}.wav"
    m4a = tmp / f"{sid}-{stem}.m4a"
    concat_wav(wav_parts, wav)
    to_m4a(wav, m4a)
    return m4a


def main():
    data = extract_verses(HTML.read_text())
    tmp = Path(tempfile.mkdtemp(prefix="lingtai-chant-"))
    try:
        staged = []
        for sutra in data:
            sid = sutra["id"]
            for i, text in enumerate(sutra["verses"]):
                stem = f"{i:02d}"
                dest = OUT / sid / f"{stem}.m4a"
                staged_path = tmp / f"out-{sid}-{stem}.m4a"
                shutil.copy2(synth_verse(sid, stem, text, tmp), staged_path)
                staged.append((dest, staged_path))
        for sutra in data:
            folder = OUT / sutra["id"]
            folder.mkdir(parents=True, exist_ok=True)
            for old in folder.glob("*.m4a"):
                old.unlink()
        for dest, staged_path in staged:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(staged_path, dest)
            print(f"  -> {dest.relative_to(ROOT)} {dest.stat().st_size} bytes")
        VERSES_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        print("ok")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
