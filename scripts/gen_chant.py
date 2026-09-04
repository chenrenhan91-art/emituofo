#!/usr/bin/env python3
"""Pre-render sutra verses with Microsoft Xiaoxiao neural voice.

Keeps punctuation in the text so the voice pauses naturally at commas
and periods (same places as before), but synthesizes each verse as one
utterance so the tone stays continuous instead of spliced clips.
"""
import asyncio
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "index.html"
OUT = ROOT / "audio"
VERSES_JSON = ROOT / "audio/verses.json"

VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "-14%"
PITCH = "-8Hz"


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


async def edge_mp3(text: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    last = None
    for attempt in range(5):
        try:
            communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
            await communicate.save(str(dest))
            if dest.exists() and dest.stat().st_size > 800:
                return
            last = RuntimeError(f"empty audio for {dest}")
        except Exception as err:  # noqa: BLE001 — retry flaky edge-tts
            last = err
        await asyncio.sleep(1.1 * (attempt + 1))
    raise RuntimeError(f"edge-tts failed for {dest}: {last}")


def to_m4a(mp3: Path, m4a: Path):
    wav = mp3.with_suffix(".wav")
    to_wav = subprocess.run(
        ["afconvert", "-f", "WAVE", "-d", "LEI16@22050", str(mp3), str(wav)],
        capture_output=True,
        text=True,
    )
    if to_wav.returncode != 0 or not wav.exists():
        raise RuntimeError(f"mp3->wav failed {mp3}: {(to_wav.stderr or '')[-400:]}")
    to_aac = subprocess.run(
        ["afconvert", "-f", "m4af", "-d", "aac", "-b", "64000", str(wav), str(m4a)],
        capture_output=True,
        text=True,
    )
    wav.unlink(missing_ok=True)
    if to_aac.returncode != 0 or not m4a.exists():
        raise RuntimeError(f"wav->m4a failed {m4a}: {(to_aac.stderr or '')[-400:]}")


async def synth_verse(sid: str, stem: str, text: str, tmp: Path) -> Path:
    print(f"synth {sid}/{stem} {text[:28]}")
    mp3 = tmp / f"{sid}-{stem}.mp3"
    m4a = tmp / f"{sid}-{stem}.m4a"
    await edge_mp3(text, mp3)
    to_m4a(mp3, m4a)
    return m4a


async def amain():
    data = extract_verses(HTML.read_text())
    tmp = Path(tempfile.mkdtemp(prefix="lingtai-chant-"))
    gate = asyncio.Semaphore(1)

    async def one(sid, i, text):
        stem = f"{i:02d}"
        async with gate:
            staged = tmp / f"out-{sid}-{stem}.m4a"
            shutil.copy2(await synth_verse(sid, stem, text, tmp), staged)
            return OUT / sid / f"{stem}.m4a", staged

    try:
        jobs = [
            one(sutra["id"], i, text)
            for sutra in data
            for i, text in enumerate(sutra["verses"])
        ]
        staged = await asyncio.gather(*jobs)
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


def main():
    asyncio.run(amain())


if __name__ == "__main__":
    main()
