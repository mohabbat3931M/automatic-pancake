from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import os, uuid
from pathlib import Path
from moviepy.editor import VideoFileClip
from PIL import Image, ImageDraw, ImageFont
import openai
from dotenv import load_dotenv

# .env থেকে API Key লোড
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
THUMB_DIR = BASE_DIR / "thumbs"
SUB_DIR = BASE_DIR / "subtitles"

for d in (UPLOAD_DIR, THUMB_DIR, SUB_DIR):
    d.mkdir(exist_ok=True)

app = FastAPI(title="Bangla AI Video Creator")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/thumbs", StaticFiles(directory=str(THUMB_DIR)), name="thumbs")
app.mount("/subtitles", StaticFiles(directory=str(SUB_DIR)), name="subtitles")

@app.get("/", response_class=HTMLResponse)
async def index():
    html = """
    <html>
    <body>
    <h2>Bangla AI Video Creator</h2>
    <form action="/upload" enctype="multipart/form-data" method="post">
    <label>Author: <input name="author"/></label><br/>
    <label>Niche: <input name="niche"/></label><br/>
    <label>Language: <select name="language"><option value="bn">বাংলা</option></select></label><br/><br/>
    <input name="file" type="file"/>
    <button type="submit">Upload</button>
    </form>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.post("/upload")
async def upload_video(author: str = Form(...), niche: str = Form(...), language: str = Form("bn"), file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".mp4", ".mov", ".mkv", ".webm", ".avi")):
        return JSONResponse({"error": "Please upload a video file."})
    
    uid = uuid.uuid4().hex[:12]
    filename = f"{uid}_{file.filename}"
    file_path = UPLOAD_DIR / filename

    with open(file_path, "wb") as f:
        f.write(await file.read())

    clip = VideoFileClip(str(file_path))
    duration = clip.duration
    thumb_t = min(max(1, int(duration*0.1)), int(duration-0.5))
    thumb_path = THUMB_DIR / f"{uid}_thumb.jpg"
    clip.save_frame(str(thumb_path), t=thumb_t)

    # থাম্বনেইলে টেক্সট
    thumb_overlay_path = THUMB_DIR / f"{uid}_thumb_overlay.jpg"
    gen_thumbnail_with_text(thumb_path, thumb_overlay_path, text=f"{niche} • {author}")

    # ট্রান্সক্রিপ্ট (placeholder)
    transcript = "(টেস্ট ট্রান্সক্রিপ্ট) এখানে অডিও থেকে পাওয়া ট্রান্সক্রিপ্ট দেখাবে।"
    srt_file = SUB_DIR / f"{uid}.srt"
    srt_file.write_text(f"1\n00:00:00,000 --> 00:00:59,000\n{transcript}\n", encoding="utf-8")

    # স্ক্রিপ্ট, ক্যাপশন, হুক জেনারেশন (placeholder)
    gen = {
        "script": f"হুক: এই ভিডিওতে আমি বলব {niche} সম্পর্কে...\nশেষ: {author} শেষ করল।",
        "captions": {"playful": "মজা করো 😄", "emotional": "অনুভূতি ❤️", "informative": "তথ্য 📌"},
        "hooks": ["আমি তোমাকে বলতে এসেছি...", "আজ দেখাব...", "জানি না তুমি শুনবে কি না..."],
        "hashtags": ["#BanglaReels", "#BanglaAI", "#CreatorBuddy"]
    }

    return JSONResponse({
        "video_filename": filename,
        "thumbnail_url": f"/thumbs/{thumb_overlay_path.name}",
        "srt_file": f"/subtitles/{srt_file.name}",
        "script": gen["script"],
        "captions": gen["captions"],
        "hooks": gen["hooks"],
        "hashtags": gen["hashtags"]
    })

def gen_thumbnail_with_text(src_path: Path, dst_path: Path, text: str = "CreatorBuddy"):
    im = Image.open(src_path).convert("RGB")
    w, h = im.size
    draw = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("arial.ttf", int(h*0.09))
    except:
        font = ImageFont.load_default()
    txt_w, txt_h = draw.textsize(text, font=font)
    margin = 10
    box_h = txt_h + margin*2
    box_y = h - box_h - 20
    rectangle = Image.new("RGBA", (w, box_h), (0,0,0,140))
    im.paste(rectangle, (0, box_y), rectangle)
    draw.text(((w-txt_w)/2, box_y+margin), text, fill=(255,255,255), font=font)
    im.save(dst_path, "JPEG", quality=85)
