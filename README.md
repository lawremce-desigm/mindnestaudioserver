# MindNest Audio Server

A FastAPI application that transcribes audio files using Whisper and generates summaries using OpenRouter.

## Features
- Transcribes audio files using faster-whisper
- Generates summaries of transcribed content using OpenRouter
- Simple web interface for testing the API

## API Endpoints
- `POST /process_audio` - Process an audio file from a URL
- `GET /` - Health check endpoint

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   Create a `.env` file with your OpenRouter API key:
   ```
   OPENROUTER_API_KEY=your_api_key_here
   ```

3. Run the server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## Docker

To run with Docker:
```bash
docker build -t mindnest-audio-server .
docker run -p 8000:8000 mindnest-audio-server
```