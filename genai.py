import os
import base64
import time
import tempfile
from typing import List, Union

from openai import OpenAI

# MoviePy import (support both old and new versions)
try:
    from moviepy.editor import VideoFileClip
except Exception:
    from moviepy import VideoFileClip  # fallback

import PyPDF2
from docx import Document


class GenAI:
    """
    Lightweight wrapper around the OpenAI API for:
    - chat text generation
    - vision (image + sampled video frames)
    - text-to-speech
    - simple document reading utilities
    """

    def __init__(self, openai_api_key: str):
        if not openai_api_key or not isinstance(openai_api_key, str):
            raise ValueError(
                "OpenAI API key is missing. Set OPENAI_API_KEY in environment variables "
                "or Streamlit Secrets."
            )

        # New SDK pattern
        self.client = OpenAI(api_key=openai_api_key)
        self.openai_api_key = openai_api_key

    # -----------------------------
    # Text / Chat
    # -----------------------------
    def generate_text(
        self,
        prompt: str,
        instructions: str = "You are a helpful AI named Jarvis",
        model: str = "gpt-4o-mini",
        output_type: str = "text",
        temperature: float = 1.0,
    ) -> str:
        completion = self.client.chat.completions.create(
            model=model,
            temperature=temperature,
            response_format={"type": output_type},
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": prompt},
            ],
        )
        response = completion.choices[0].message.content or ""
        return response.replace("```html", "").replace("```", "")

    def generate_chat_response(
        self,
        chat_history: List[dict],
        instructions: str,
        model: str = "gpt-4o-mini",
        output_type: str = "text",
    ) -> str:
        completion = self.client.chat.completions.create(
            model=model,
            response_format={"type": output_type},
            messages=[
                {"role": "system", "content": instructions},
                *chat_history,
            ],
        )
        return completion.choices[0].message.content or ""

    # -----------------------------
    # Images / Vision
    # -----------------------------
    @staticmethod
    def encode_image(image_path: str) -> str:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def generate_image_description(
        self,
        image_paths: Union[str, List[str]],
        instructions: str,
        model: str = "gpt-4o-mini",
        max_tokens: int = 1000,
    ) -> str:
        if isinstance(image_paths, str):
            image_paths = [image_paths]

        image_urls = [
            f"data:image/jpeg;base64,{self.encode_image(p)}" for p in image_paths
        ]

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": instructions},
                    *[
                        {"type": "image_url", "image_url": {"url": url}}
                        for url in image_urls
                    ],
                ],
            }
        ]

        completion = self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
        )

        response = completion.choices[0].message.content or ""
        return response.replace("```html", "").replace("```", "")

    def generate_video_description(
        self,
        video_path: str,
        instructions: str,
        model: str = "gpt-4o-mini",
        n_frames: int = 10,
    ) -> str:
        """
        Sample frames uniformly from video and describe based on those frames.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")

        # Use a temp dir that auto-cleans
        with tempfile.TemporaryDirectory() as temp_dir:
            image_paths = []

            video = VideoFileClip(video_path)
            try:
                duration = float(video.duration) if video.duration else 0.0
                if duration <= 0:
                    raise ValueError("Video duration is 0; cannot sample frames.")

                # Avoid repeated timestamps for short videos
                if n_frames <= 1:
                    timestamps = [0.0]
                else:
                    timestamps = [i * duration / (n_frames - 1) for i in range(n_frames)]

                for i, t in enumerate(timestamps):
                    frame_path = os.path.join(temp_dir, f"frame_{i:03d}.jpg")
                    video.save_frame(frame_path, t=t)
                    image_paths.append(frame_path)

            finally:
                # Always close to release resources
                video.close()

            return self.generate_image_description(image_paths, instructions, model=model)

    # -----------------------------
    # Text-to-Speech
    # -----------------------------
    def generate_audio(
        self,
        text: str,
        file_path: str,
        model: str = "gpt-4o-mini-tts",
        voice: str = "nova",
        speed: float = 1.0,
    ) -> bool:
        if not text or not text.strip():
            raise ValueError("Cannot generate audio from empty text.")

        response = self.client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            speed=speed,
        )
        response.stream_to_file(file_path)
        return True

    # -----------------------------
    # Document helpers
    # -----------------------------
    @staticmethod
    def read_pdf(file_path: str) -> str:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return "".join((page.extract_text() or "") for page in reader.pages)

    @staticmethod
    def read_docx(file_path: str) -> str:
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs)
