#!/usr/bin/env python3
"""Pre-render sutra verses with Piper, pausing at punctuation like recitation."""
import json
import re
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPER = Path.home() / "Library/Python/3.9/bin/piper"
MODEL = ROOT / "voices/zh_CN-huayan-medium.onnx"
HTML = ROOT / "index.html"
OUT = ROOT / "audio"
VERSES_JSON = ROOT / "audio/verses.json"

DEFAULT_SCALE = 1.20
MANTRA_SCALE = 1.28

PAUSE = {
    "，": 0.28,
    "、": 0.22,
    "：": 0.32,
    "；": 0.38,
    "。": 0.52,
    "！": 0.52,
    "？": 0.48,
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
                pause = PAUSE[ch]
                spoken = re.sub(r"\W+", "", part)
                if ch in "。！？" and len(spoken) <= 8:
                    pause = min(pause, 0.32)
                chunks.append((part, pause))
            buf = ""
    if buf.strip():
        chunks.append((buf.strip(), 0.18))
    return chunks or [(text, 0.18)]


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


def piper_wav(text: str, dest: Path, length_scale: float):
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [
            str(PIPER),
            "-m", str(MODEL),
            "-f", str(dest),
            "--length-scale", str(length_scale),
            "--sentence-silence", "0.02",
            "--noise-scale", "0.5",
            "--volume", "1.0",
        ],
        input=text + "\n",
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0 or not dest.exists() or dest.stat().st_size < 800:
        raise RuntimeError(f"piper failed for {dest}: {(proc.stderr or '')[-400:]}")


def to_m4a(wav: Path, m4a: Path):
    subprocess.run(
        ["afconvert", "-f", "m4af", "-d", "aac", "-b", "64000", str(wav), str(m4a)],
        check=True,
        capture_output=True,
    )


def main():
    if not PIPER.exists():
        raise SystemExit(f"piper not found: {PIPER}")
    data = extract_verses(HTML.read_text())
    VERSES_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    tmp = Path(tempfile.mkdtemp(prefix="lingtai-chant-"))
    try:
        for sutra in data:
            sid = sutra["id"]
            scale = MANTRA_SCALE if sid == "dabei_mantra" else DEFAULT_SCALE
            folder = OUT / sid
            if folder.exists():
                for old in folder.glob("*.m4a"):
                    old.unlink()
            folder.mkdir(parents=True, exist_ok=True)
            for i, text in enumerate(sutra["verses"]):
                stem = f"{i:02d}"
                m4a = folder / f"{stem}.m4a"
                clauses = split_clauses(text)
                wav_parts = []
                for j, (clause, gap) in enumerate(clauses):
                    part = tmp / f"{sid}-{stem}-{j}.wav"
                    print(f"synth {sid}/{stem} [{j+1}/{len(clauses)}] {clause[:24]}")
                    piper_wav(clause, part, scale)
                    wav_parts.append((part, gap))
                wav = tmp / f"{sid}-{stem}.wav"
                concat_wav(wav_parts, wav)
                to_m4a(wav, m4a)
                print(f"  -> {m4a.relative_to(ROOT)} {m4a.stat().st_size} bytes")
        print("ok")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
