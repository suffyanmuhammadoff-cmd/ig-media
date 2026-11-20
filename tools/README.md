# Daily content pipeline (Jarvis Works + Azure Cash Offers)

Setup in a fresh workspace:
```
pip install --break-system-packages kokoro-onnx soundfile pyrender trimesh
mkdir -p /home/claude/tts && cd /home/claude/tts
curl -sSLO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -sSLO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```
Render a reel: `PYOPENGL_PLATFORM=egl python3 tools/skit3d.py spec.json out.mp4` (see tools/examples/*_reel*.json for spec format; sets: garage, clinic, home_office, kitchen_leak, living_boxes, rental_damage).
Render carousel/story: `python3 tools/cards.py spec.json out_prefix` (examples: *_post*.json, *_story*.json).

Media goes in azure/ or jarvis/, gets committed, then is referenced via
https://cdn.jsdelivr.net/gh/suffyanmuhammadoff-cmd/ig-media@<commit-sha>/<path>

Queue: n8n data table `ig_queue` (id W7LX7dXCiRFBF5nj, project iELpxYvtIe7RyxV1).
Columns: account (azure|jarvis), kind (reel|story|carousel), media_urls (comma-separated), caption, post_after (ISO with -05:00), status=queued, result="".
Posters: "IG Poster - azure.cashoffers" and "IG Poster - jarvisworks.ai" run every 20 min and publish due rows.
