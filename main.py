from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from faster_whisper import WhisperModel
import requests
import tempfile
import os
import urllib.parse
from dotenv import load_dotenv

# Load .env file
load_dotenv()

app = FastAPI()

# Load Whisper model once (tiny=fast, small/medium=better accuracy)
model = WhisperModel("tiny")

# Request schema
class AudioRequest(BaseModel):
    audio_url: str


# ---- Summarization Helper (OpenRouter) ----
def summarize_with_openrouter(text: str) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return "Error: OPENROUTER_API_KEY not set. Please configure the environment variable."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "z-ai/glm-4.5-air:free",  # You can swap to another model
        "messages": [
            {
                "role": "system",
                "content": "You are an assistant that summarizes lecture transcripts into concise notes.",
            },
            {"role": "user", "content": f"Summarize this lecture:\n{text}"},
        ],
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Summary failed: {e}"


# ---- API Route ----
@app.post("/process_audio")
async def process_audio(req: AudioRequest):
    tmp_path = None
    try:
        # 1. Detect extension from URL (default .m4a if none found)
        ext = os.path.splitext(urllib.parse.urlparse(req.audio_url).path)[1] or ".m4a"
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp_path = tmp.name

        # 2. Download audio file
        audio_response = requests.get(req.audio_url, timeout=180)
        audio_response.raise_for_status()
        with open(tmp_path, "wb") as f:
            f.write(audio_response.content)

        # 3. Transcribe with Whisper
        segments, info = model.transcribe(tmp_path)
        transcript = " ".join([s.text for s in segments])

        # 4. Summarize with OpenRouter
        summary = summarize_with_openrouter(transcript)

        # 5. Clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

        # 6. Return result immediately
        return {
            "status": "success",
            "language": info.language,
            "transcript": transcript,
            "summary": summary,
        }

    except Exception as e:
        # Clean up temp file if it exists
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {
        "message": "Audio Processing API - Send POST request to /process_audio with {'audio_url': 'url'}"
    }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)