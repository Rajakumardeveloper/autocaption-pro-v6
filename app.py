import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask
from faster_whisper import WhisperModel

try:
    from indic_transliteration import sanscript
except ImportError:
    sanscript = None

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

# Small is a practical CPU default. You can set WHISPER_MODEL=medium or
# WHISPER_MODEL=large-v3 before starting the app when you want higher accuracy.
MODEL_SIZE = os.getenv("WHISPER_MODEL", "small")
DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "500"))

app = FastAPI(title="AutoCaption AI")

model = WhisperModel(
    MODEL_SIZE,
    device=DEVICE,
    compute_type=COMPUTE_TYPE,
)


# =========================================================
# CREATOR CAPTION TEMPLATES
# =========================================================

CAPTION_TEMPLATES = {
    "bold_white": dict(
        font_name="Impact",
        text_color="#FFFFFF",
        background_color="#000000",
        background_opacity=0,
        outline_color="#000000",
        outline_width=4,
        shadow=2,
        bold=True,
        italic=False,
        font_size=58,
        border_style=1,
        highlight=False,
        highlight_color="#FFE600",
    ),
    "white_yellow": dict(
        font_name="Impact",
        text_color="#FFFFFF",
        background_color="#000000",
        background_opacity=0,
        outline_color="#000000",
        outline_width=4,
        shadow=2,
        bold=True,
        italic=False,
        font_size=58,
        border_style=1,
        highlight=True,
        highlight_color="#FFE600",
    ),
    "yellow_glow": dict(
        font_name="Impact",
        text_color="#FFE600",
        background_color="#000000",
        background_opacity=0,
        outline_color="#6D5E00",
        outline_width=2,
        shadow=4,
        bold=True,
        italic=False,
        font_size=58,
        border_style=1,
        highlight=False,
        highlight_color="#FFFFFF",
    ),
    "creator_bold": dict(
        font_name="Impact",
        text_color="#FFFFFF",
        background_color="#000000",
        background_opacity=0,
        outline_color="#000000",
        outline_width=6,
        shadow=3,
        bold=True,
        italic=False,
        font_size=64,
        border_style=1,
        highlight=True,
        highlight_color="#FFD400",
    ),
    "clean_white": dict(
        font_name="Arial",
        text_color="#FFFFFF",
        background_color="#000000",
        background_opacity=0,
        outline_color="#111111",
        outline_width=2,
        shadow=2,
        bold=False,
        italic=False,
        font_size=52,
        border_style=1,
        highlight=False,
        highlight_color="#FFFFFF",
    ),
    "yellow_bold": dict(
        font_name="Impact",
        text_color="#FFD800",
        background_color="#000000",
        background_opacity=0,
        outline_color="#000000",
        outline_width=5,
        shadow=2,
        bold=True,
        italic=False,
        font_size=60,
        border_style=1,
        highlight=False,
        highlight_color="#FFFFFF",
    ),
    "black_box": dict(
        font_name="Arial",
        text_color="#FFFFFF",
        background_color="#000000",
        background_opacity=82,
        outline_color="#000000",
        outline_width=0,
        shadow=0,
        bold=True,
        italic=False,
        font_size=52,
        border_style=3,
        highlight=True,
        highlight_color="#FFE600",
    ),
    "white_box": dict(
        font_name="Arial",
        text_color="#111111",
        background_color="#FFFFFF",
        background_opacity=88,
        outline_color="#FFFFFF",
        outline_width=0,
        shadow=0,
        bold=True,
        italic=False,
        font_size=50,
        border_style=3,
        highlight=False,
        highlight_color="#111111",
    ),
    "red_alert": dict(
        font_name="Impact",
        text_color="#FF3B30",
        background_color="#000000",
        background_opacity=0,
        outline_color="#000000",
        outline_width=4,
        shadow=2,
        bold=True,
        italic=False,
        font_size=58,
        border_style=1,
        highlight=False,
        highlight_color="#FFFFFF",
    ),
    "cyan_pop": dict(
        font_name="Impact",
        text_color="#35E7FF",
        background_color="#000000",
        background_opacity=0,
        outline_color="#000000",
        outline_width=4,
        shadow=3,
        bold=True,
        italic=False,
        font_size=58,
        border_style=1,
        highlight=False,
        highlight_color="#FFFFFF",
    ),
    "blue_electric": dict(
        font_name="Arial",
        text_color="#4EA1FF",
        background_color="#000000",
        background_opacity=0,
        outline_color="#081B4A",
        outline_width=4,
        shadow=4,
        bold=True,
        italic=False,
        font_size=56,
        border_style=1,
        highlight=False,
        highlight_color="#FFFFFF",
    ),
    "pink_creator": dict(
        font_name="Impact",
        text_color="#FF5FD7",
        background_color="#000000",
        background_opacity=0,
        outline_color="#000000",
        outline_width=4,
        shadow=3,
        bold=True,
        italic=False,
        font_size=58,
        border_style=1,
        highlight=False,
        highlight_color="#FFFFFF",
    ),
    "soft_aesthetic": dict(
        font_name="Georgia",
        text_color="#F4F0EA",
        background_color="#303030",
        background_opacity=34,
        outline_color="#555555",
        outline_width=1,
        shadow=2,
        bold=False,
        italic=True,
        font_size=48,
        border_style=1,
        highlight=False,
        highlight_color="#FFFFFF",
    ),
    "typewriter": dict(
        font_name="Courier New",
        text_color="#FFFFFF",
        background_color="#111111",
        background_opacity=68,
        outline_color="#000000",
        outline_width=1,
        shadow=1,
        bold=False,
        italic=False,
        font_size=45,
        border_style=3,
        highlight=False,
        highlight_color="#FFFFFF",
    ),
    "minimal_shadow": dict(
        font_name="Arial",
        text_color="#FFFFFF",
        background_color="#000000",
        background_opacity=0,
        outline_color="#000000",
        outline_width=1,
        shadow=5,
        bold=False,
        italic=False,
        font_size=54,
        border_style=1,
        highlight=False,
        highlight_color="#FFFFFF",
    ),
    "news_ticker": dict(
        font_name="Arial",
        text_color="#FFFFFF",
        background_color="#D71920",
        background_opacity=94,
        outline_color="#D71920",
        outline_width=0,
        shadow=0,
        bold=True,
        italic=False,
        font_size=44,
        border_style=3,
        highlight=False,
        highlight_color="#FFFFFF",
    ),
    "purple_neon": dict(
        font_name="Arial",
        text_color="#D58CFF",
        background_color="#000000",
        background_opacity=0,
        outline_color="#54207A",
        outline_width=3,
        shadow=6,
        bold=True,
        italic=False,
        font_size=56,
        border_style=1,
        highlight=False,
        highlight_color="#FFFFFF",
    ),
    "green_focus": dict(
        font_name="Impact",
        text_color="#B8FF4A",
        background_color="#000000",
        background_opacity=0,
        outline_color="#000000",
        outline_width=4,
        shadow=3,
        bold=True,
        italic=False,
        font_size=58,
        border_style=1,
        highlight=False,
        highlight_color="#FFFFFF",
    ),
    "cream_retro": dict(
        font_name="Georgia",
        text_color="#FFF0C2",
        background_color="#402B18",
        background_opacity=26,
        outline_color="#23170D",
        outline_width=3,
        shadow=2,
        bold=True,
        italic=False,
        font_size=50,
        border_style=1,
        highlight=False,
        highlight_color="#FFFFFF",
    ),
}


DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")


def has_devanagari(text: str) -> bool:
    return bool(DEVANAGARI_RE.search(text or ""))


def romanize_hindi_word(text: str) -> str:
    """Convert Devanagari to creator-friendly Roman Hindi; leave English unchanged."""
    if not text or not has_devanagari(text):
        return text
    if sanscript is None:
        return text
    try:
        roman = sanscript.transliterate(text, sanscript.DEVANAGARI, sanscript.ITRANS)
        roman = roman.lower()
        roman = (
            roman.replace("~n", "n")
            .replace("~m", "m")
            .replace(".n", "n")
            .replace(".m", "m")
        )
        roman = re.sub(r"[^a-z0-9' -]", "", roman)
        roman = re.sub(r"\s+", " ", roman).strip()
        casual = {
            "kaise": "kese", "kaisa": "kesa", "kaisi": "kesi",
            "aise": "ese", "waise": "wese", "jaise": "jese",
            "kyun": "kyu", "nahi": "nahi", "nahin": "nahi",
            "hain": "hai", "hoon": "hu", "hu": "hu",
        }
        return casual.get(roman, roman) or text
    except Exception:
        return text


def clean_creator_word(text: str) -> str:
    """Normalize spacing/punctuation without changing the spoken language."""
    text = re.sub(r"\s+", " ", (text or "")).strip()
    return text


def maybe_romanize_words(words, mode: str):
    """Romanize Hindi script in Hinglish/auto modes while preserving English words."""
    converted = []
    for word in words:
        item = dict(word)
        if mode in {"hinglish", "auto"}:
            item["text"] = romanize_hindi_word(item["text"])
        item["text"] = clean_creator_word(item["text"])
        converted.append(item)
    return converted


def capitalize_first_word(text: str) -> str:
    """Capitalize the first alphabetic character only."""
    if not text:
        return text
    chars = list(text)
    for i, char in enumerate(chars):
        if char.isalpha():
            chars[i] = char.upper()
            break
    return "".join(chars)


def transform_chunks_language(chunks, mode: str) -> list:
    """Apply the selected output mode to caption words."""
    output = []
    for chunk in chunks:
        updated = dict(chunk)
        updated["words"] = maybe_romanize_words(chunk.get("words", []), mode)

        # Capitalize the actual first caption word, not only the joined text.
        if mode in {"hinglish", "auto"} and updated["words"]:
            first = updated["words"][0]["text"]
            updated["words"][0]["text"] = capitalize_first_word(first)

        updated["text"] = " ".join(w["text"] for w in updated["words"]).strip()
        output.append(updated)
    return output


# =========================================================
# HELPERS
# =========================================================


def cleanup_dir(path: str) -> None:
    shutil.rmtree(path, ignore_errors=True)


def find_ffmpeg() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg

    root = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    if root.is_dir():
        matches = list(root.rglob("ffmpeg.exe"))
        if matches:
            return str(matches[0])

    raise FileNotFoundError("FFmpeg executable not found.")


def safe_ass_text(text: str) -> str:
    return (
        text.replace("\\", r"\\")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace("\n", r"\N")
    )


def ass_time(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        centis = 0
        secs += 1
    if secs >= 60:
        secs -= 60
        minutes += 1
    if minutes >= 60:
        minutes -= 60
        hours += 1
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def ass_color(hex_color: str, alpha: int = 0) -> str:
    value = (hex_color or "#FFFFFF").strip().lstrip("#")
    if len(value) != 6 or not all(c in "0123456789abcdefABCDEF" for c in value):
        value = "FFFFFF"
    r, g, b = value[0:2], value[2:4], value[4:6]
    alpha = max(0, min(255, int(alpha)))
    return f"&H{alpha:02X}{b}{g}{r}"


def line_break_texts(words, max_chars_per_line: int) -> tuple[list[str], int]:
    """Return a balanced 1- or 2-line word split and its split point."""
    texts = [clean_creator_word(w) for w in words if clean_creator_word(w)]
    if not texts:
        return [], 0
    if len(" ".join(texts)) <= max_chars_per_line:
        return texts, len(texts)

    best = None
    best_score = 10**9
    for split in range(1, len(texts)):
        left = " ".join(texts[:split])
        right = " ".join(texts[split:])
        if len(left) <= max_chars_per_line and len(right) <= max_chars_per_line:
            score = abs(len(left) - len(right))
            if score < best_score:
                best = (texts, split)
                best_score = score
    if best:
        return best

    # For a single very long word, keep it intact. It is safer than creating a 3rd line.
    first = []
    second = []
    length = 0
    for word in texts:
        add = len(word) + (1 if first else 0)
        if first and length + add > max_chars_per_line:
            second.append(word)
        else:
            first.append(word)
            length += add
    return texts if not second else (texts, len(first))


def wrap_caption(text: str, max_chars_per_line: int = 26) -> str:
    words = text.split()
    if not words:
        return ""
    _, split = line_break_texts(words, max_chars_per_line)
    left = " ".join(words[:split])
    right = " ".join(words[split:])
    if not right:
        return left
    return left + r"\N" + right


def make_caption_chunks(segments):
    """Fast-speech friendly phrase chunks based on Whisper word timestamps."""
    MAX_WORDS = 6
    MAX_CHARS = 48
    MIN_DURATION = 0.42
    MAX_DURATION = 2.15
    PAUSE_BREAK = 0.22

    chunks = []

    for segment in segments:
        words = []
        for word in (getattr(segment, "words", None) or []):
            txt = (getattr(word, "word", "") or "").strip()
            start = getattr(word, "start", None)
            end = getattr(word, "end", None)
            if txt and start is not None and end is not None:
                words.append({"text": txt, "start": float(start), "end": float(end)})

        if not words:
            raw_text = " ".join(segment.text.strip().split())
            if not raw_text:
                continue
            raw_words = raw_text.split()
            duration = max(float(segment.end) - float(segment.start), 0.25)
            per_word = duration / max(len(raw_words), 1)
            for i, word in enumerate(raw_words):
                words.append({
                    "text": word,
                    "start": float(segment.start) + i * per_word,
                    "end": float(segment.start) + (i + 1) * per_word,
                })

        current = []

        def flush():
            nonlocal current
            if not current:
                return
            start = current[0]["start"]
            end = current[-1]["end"]
            text = " ".join(w["text"] for w in current).strip()
            if text and end > start:
                chunks.append({
                    "start": start,
                    "end": max(end, start + MIN_DURATION),
                    "text": text,
                    "words": list(current),
                })
            current = []

        for word in words:
            if not current:
                current = [word]
                continue

            candidate = current + [word]
            candidate_text = " ".join(w["text"] for w in candidate)
            candidate_duration = candidate[-1]["end"] - candidate[0]["start"]
            pause = word["start"] - current[-1]["end"]
            long_word = len(word["text"].strip()) > 26

            must_break = (
                len(candidate) > MAX_WORDS
                or len(candidate_text) > MAX_CHARS
                or candidate_duration > MAX_DURATION
                or pause >= PAUSE_BREAK
                or long_word and len(current) >= 2
            )

            if must_break:
                flush()
                current = [word]
            else:
                current.append(word)

        flush()

    # Clip overlaps and remove tiny pieces created by aggressive splitting.
    final = []
    for i, chunk in enumerate(chunks):
        if i + 1 < len(chunks):
            chunk["end"] = min(chunk["end"], chunks[i + 1]["start"])
        if chunk["end"] - chunk["start"] >= 0.34:
            chunk["text"] = " ".join(chunk["text"].split())
            final.append(chunk)

    return final


# =========================================================
# ASS STYLE RENDERING
# =========================================================


def render_highlighted_text(chunk: dict, active_index: int, style: dict, max_chars: int) -> str:
    """Render exactly one caption event with one active word highlighted.

    The previous implementation drew a normal caption event and then drew a
    second overlay event. That could make captions look duplicated/stacked.
    This version renders a single event for each active word interval.
    """
    words = chunk.get("words", [])
    texts = [w.get("text", "") for w in words]
    _, split = line_break_texts(texts, max_chars)

    base_colour = ass_color(style["text_color"])
    highlight_colour = ass_color(style["highlight_color"])

    def render_word(index: int, word: dict) -> str:
        safe = safe_ass_text(word.get("text", ""))
        if index == active_index:
            return "{" + f"\\1c{highlight_colour}" + "}" + safe + "{" + f"\\1c{base_colour}" + "}"
        return safe

    first = words[:split]
    second = words[split:]

    first_text = " ".join(
        render_word(i, word)
        for i, word in enumerate(first)
    )

    if not second:
        return first_text

    second_text = " ".join(
        render_word(split + i, word)
        for i, word in enumerate(second)
    )
    return first_text + r"\N" + second_text


def write_ass(
    chunks,
    out_path: Path,
    font_size: int,
    position_percent: int,
    style: dict,
) -> None:
    # 10% is near the top, 90% near the bottom. Keep a safe margin from edges.
    position_percent = max(10, min(90, int(position_percent)))
    y = round(130 + (position_percent / 100.0) * 820)
    max_chars = max(18, min(28, round(27 * 54 / max(font_size, 34))))
    bg_alpha = round(255 * (100 - int(style["background_opacity"])) / 100)

    header = f"""[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nScaledBorderAndShadow: yes\nWrapStyle: 2\nYCbCr Matrix: TV.709\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,{style['font_name']},{font_size},{ass_color(style['text_color'])},{ass_color(style['text_color'])},{ass_color(style['outline_color'])},{ass_color(style['background_color'], bg_alpha)},{-1 if style['bold'] else 0},{1 if style['italic'] else 0},0,0,100,100,0,0,{style['border_style']},{style['outline_width']},{style['shadow']},5,120,120,0,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"""

    lines = [header]
    for chunk in chunks:
        if not chunk.get("words"):
            continue
        display_text = wrap_caption(chunk["text"], max_chars)
        if not display_text:
            continue
        pos_tag = f"{{\\an5\\pos(960,{y})}}"
        start = ass_time(chunk["start"])
        end = ass_time(chunk["end"])

        # For highlight templates, render ONLY the highlighted version.
        # Do not also render the plain caption underneath it; that was the
        # source of the apparent double/overlapping captions.
        if style.get("highlight") and len(chunk.get("words", [])) > 1:
            words = chunk["words"]
            for idx, word in enumerate(words):
                active_start = max(chunk["start"], float(word["start"]))
                if idx + 1 < len(words):
                    active_end = min(chunk["end"], float(words[idx + 1]["start"]))
                else:
                    active_end = chunk["end"]
                if active_end <= active_start:
                    continue
                highlighted = render_highlighted_text(chunk, idx, style, max_chars)
                lines.append(
                    f"Dialogue: 0,{ass_time(active_start)},{ass_time(active_end)},Default,,0,0,0,,{pos_tag}{highlighted}\n"
                )
        else:
            lines.append(
                f"Dialogue: 0,{start},{end},Default,,0,0,0,,{pos_tag}{display_text}\n"
            )

    out_path.write_text("".join(lines), encoding="utf-8")


# =========================================================
# AUDIO NORMALIZATION
# =========================================================


def extract_audio_for_transcription(input_path: Path, workdir: Path) -> Path:
    """Normalize all source audio to mono 16 kHz PCM for more reliable recognition."""
    ffmpeg = find_ffmpeg()
    audio_path = workdir / "speech.wav"
    cmd = [
        ffmpeg, "-y", "-i", str(input_path),
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
        str(audio_path),
    ]
    completed = subprocess.run(cmd, cwd=str(workdir), capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(
            "Could not extract audio for transcription.\n" + completed.stderr[-5000:]
        )
    if not audio_path.exists() or audio_path.stat().st_size < 1024:
        raise RuntimeError("The uploaded video does not contain usable audio.")
    return audio_path


# =========================================================
# FFMPEG
# =========================================================


def run_ffmpeg(input_path: Path, ass_path: Path, output_path: Path, volume_percent: int = 100) -> None:
    ffmpeg = find_ffmpeg()
    volume_percent = max(0, min(200, int(volume_percent)))
    volume = volume_percent / 100.0

    cmd = [
        ffmpeg, "-y", "-i", str(input_path),
        "-vf", f"subtitles=filename='{ass_path.name}'",
        "-map", "0:v:0", "-map", "0:a:0?",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p",
    ]
    if volume_percent != 100:
        cmd += ["-af", f"volume={volume:.2f}"]
    cmd += [
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", str(output_path),
    ]

    completed = subprocess.run(cmd, cwd=str(ass_path.parent), capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr[-6000:])


# =========================================================
# API
# =========================================================


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "model": MODEL_SIZE,
        "device": DEVICE,
        "compute_type": COMPUTE_TYPE,
    }


@app.post("/api/caption")
async def caption_video(
    video: UploadFile = File(...),
    language: Optional[str] = Form(None),
    font_size: int = Form(54),
    position: str = Form("bottom"),
    position_percent: int = Form(78),
    template: str = Form("bold_white"),
    audio_volume: int = Form(100),
    hotwords: str = Form(""),
):
    if not video.filename:
        raise HTTPException(status_code=400, detail="Please choose a video file.")

    if template not in CAPTION_TEMPLATES:
        template = "bold_white"
    style = dict(CAPTION_TEMPLATES[template])

    # Backward-compatible position presets.
    if position not in {"top", "bottom"}:
        position = "bottom"
    try:
        position_percent = int(position_percent)
    except (TypeError, ValueError):
        position_percent = 78 if position == "bottom" else 18
    position_percent = max(10, min(90, position_percent))

    try:
        requested_size = int(font_size)
    except (TypeError, ValueError):
        requested_size = style["font_size"]
    font_size = style["font_size"] if requested_size == 54 else max(32, min(80, requested_size))

    try:
        audio_volume = int(audio_volume)
    except (TypeError, ValueError):
        audio_volume = 100
    audio_volume = max(0, min(200, audio_volume))

    workdir = Path(tempfile.mkdtemp(prefix="autocaption_"))
    suffix = Path(video.filename).suffix.lower() or ".mp4"
    input_path = workdir / f"input{suffix}"
    subtitle_path = workdir / "captions.ass"
    output_path = workdir / f"captioned-{uuid.uuid4().hex[:8]}.mp4"

    try:
        total = 0
        with input_path.open("wb") as f:
            while chunk := await video.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_UPLOAD_MB * 1024 * 1024:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Video is too large. Maximum size is {MAX_UPLOAD_MB} MB.",
                    )
                f.write(chunk)

        audio_path = extract_audio_for_transcription(input_path, workdir)

        requested_mode = (language or "auto").strip().lower()
        if requested_mode not in {"auto", "hinglish", "hi", "en"}:
            requested_mode = "auto"

        transcribe_kwargs = {
            "beam_size": 7,
            "best_of": 5,
            "patience": 1.0,
            "vad_filter": True,
            "vad_parameters": {
                "min_silence_duration_ms": 350,
                "speech_pad_ms": 180,
            },
            "condition_on_previous_text": True,
            "word_timestamps": True,
            "multilingual": True,
            "language_detection_segments": 5,
            "language_detection_threshold": 0.35,
            "initial_prompt": (
                "Indian creator speech. Hindi, English and Hinglish can be mixed. "
                "Keep English words in English. Recognize Hindi accurately. "
                "Do not translate. Preserve names, brands, slang, numbers and technical terms. "
                "Examples: Hello guys kese ho, Aaj hum ek important topic discuss karenge."
            ),
        }

        if hotwords.strip():
            transcribe_kwargs["hotwords"] = hotwords.strip()[:1000]

        if requested_mode == "hi":
            transcribe_kwargs["language"] = "hi"
            transcribe_kwargs["multilingual"] = False
        elif requested_mode == "en":
            transcribe_kwargs["language"] = "en"
            transcribe_kwargs["multilingual"] = False

        segments_iter, info = model.transcribe(str(audio_path), **transcribe_kwargs)
        segments = list(segments_iter)

        if not segments:
            raise HTTPException(status_code=422, detail="No speech was detected in the video.")

        chunks = make_caption_chunks(segments)
        if not chunks:
            raise HTTPException(status_code=422, detail="Could not create captions.")

        # Auto and Hinglish output use Roman Hindi whenever Whisper returned Hindi script.
        if requested_mode in {"auto", "hinglish"}:
            chunks = transform_chunks_language(chunks, requested_mode)

        write_ass(
            chunks,
            subtitle_path,
            font_size,
            position_percent,
            style,
        )

        run_ffmpeg(
            input_path,
            subtitle_path,
            output_path,
            audio_volume,
        )

        return FileResponse(
            output_path,
            media_type="video/mp4",
            filename=f"captioned-{Path(video.filename).stem}.mp4",
            background=BackgroundTask(cleanup_dir, str(workdir)),
            headers={
                "X-Detected-Language": getattr(info, "language", "unknown") or "unknown",
                "X-Caption-Mode": requested_mode,
            },
        )

    except HTTPException:
        cleanup_dir(str(workdir))
        raise
    except FileNotFoundError:
        cleanup_dir(str(workdir))
        raise HTTPException(status_code=500, detail="FFmpeg is not installed or not available on PATH.")
    except Exception as exc:
        cleanup_dir(str(workdir))
        raise HTTPException(status_code=500, detail=f"Processing failed: {exc}")
    finally:
        await video.close()


app.mount(
    "/",
    StaticFiles(directory=STATIC_DIR, html=True),
    name="static",
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
