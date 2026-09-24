# AutoCaption AI — Pro Multilingual Creator Captions

Local FastAPI + faster-whisper + FFmpeg app for exporting creator-style captions.

## Included in v5

- English + Hindi + Hinglish caption modes
- Auto code-switch handling with multilingual faster-whisper
- Roman-Hindi output for Hinglish/Auto when Hindi script is detected
- Short phrase captions with word timestamps and safe 1–2 line wrapping
- 18 creator templates
- Vertical caption-position control plus quick top/center/bottom presets
- Caption size control
- Optional word hints for names, brands, slang and technical terms
- Original-video preview with audio and volume control
- Export audio volume control (0–200%)
- Processed-video preview with audio and volume control
- Responsive mobile/desktop layout

## Windows

```powershell
pip install -r requirements.txt
python -m py_compile .\app.py
python app.py
```

Open http://127.0.0.1:8000

## Higher transcription quality

Set `WHISPER_MODEL=medium` or `WHISPER_MODEL=large-v3` before starting the server. Larger models require more RAM and are slower on CPU.

The app uses faster-whisper multilingual mode for Auto/Hinglish, which supports per-segment language detection and word-level timestamps.


## v6 fixes

- Highlight templates render one caption event at a time, removing double/overlapping captions.
- Source and exported video previews explicitly enable audio and provide play/pause audio controls.
- First caption words are capitalized in Auto/Hinglish mode at the word level.
