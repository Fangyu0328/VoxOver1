import os
import tempfile
from functools import lru_cache

from dotenv import load_dotenv
from genai import GenAI

# MoviePy import (support both old and new versions)
try:
    from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
except Exception:
    from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip  # fallback


# Load .env for local development (Streamlit Cloud won't have it, and that's fine)
load_dotenv()


def _get_secret(name: str, default=None):
    """
    Try Streamlit secrets first (cloud), then fall back to env vars (local/.env).
    This function avoids hard dependency on streamlit for local scripts.
    """
    value = os.getenv(name, default)
    try:
        import streamlit as st
        value = st.secrets.get(name, value)
    except Exception:
        pass
    return value


def _get_openai_api_key() -> str:
    key = _get_secret("OPENAI_API_KEY")
    return key


@lru_cache(maxsize=1)
def _jarvis() -> GenAI:
    """
    Lazily create and cache the GenAI client.
    This prevents Streamlit Cloud from crashing at import time.
    """
    key = _get_openai_api_key()
    if not key:
        raise RuntimeError(
            "Missing OPENAI_API_KEY. On Streamlit Cloud: add it in App Settings → Secrets as "
            'OPENAI_API_KEY = "your_key". Locally: set env var or use a .env file.'
        )
    return GenAI(key)


def get_video_duration(video_path: str) -> float:
    """Return video duration in seconds."""
    clip = VideoFileClip(video_path)
    try:
        return float(clip.duration)
    finally:
        clip.close()


def generate_voiceover_text(video_path: str, instructions: str) -> str:
    """
    Analyzes a video and generates voiceover text based on user instructions.
    """
    wps = 200 / 60  # 200 words per minute / 60 seconds
    duration_secs = get_video_duration(video_path)
    nwords_max = wps * duration_secs

    instructions_modified = (
        instructions
        + f"\nYour voiceover text should be less than {nwords_max:.0f} words long. "
        + "Do not use any hashtags or emojis in the voiceover text as this will be read aloud."
    )

    jarvis = _jarvis()
    voiceover_text = jarvis.generate_video_description(
        video_path,
        instructions_modified,
        model="gpt-4o-mini",
    )
    return voiceover_text


def generate_voiceover_audio(
    voiceover_text: str,
    file_path: str,
    voice_name: str = "nova",
    speed: float = 1.0,
):
    """
    Converts text to speech and saves as audio file.
    """
    jarvis = _jarvis()
    return jarvis.generate_audio(
        voiceover_text,
        file_path,
        model="gpt-4o-mini-tts",
        voice=voice_name,
        speed=speed,
    )


def _scale_volume(audio_clip, volume: float):
    """Compatibility helper across MoviePy versions."""
    if volume == 1.0 or audio_clip is None:
        return audio_clip
    if hasattr(audio_clip, "with_volume_scaled"):
        return audio_clip.with_volume_scaled(volume)  # MoviePy v2+
    if hasattr(audio_clip, "volumex"):
        return audio_clip.volumex(volume)  # MoviePy v1
    return audio_clip


def _subclip(audio_clip, t_end: float):
    """Compatibility helper across MoviePy versions."""
    if audio_clip is None:
        return None
    if hasattr(audio_clip, "subclipped"):
        return audio_clip.subclipped(0, t_end)  # MoviePy v2+
    return audio_clip.subclip(0, t_end)  # MoviePy v1


def _set_audio(video_clip, audio_clip):
    """Compatibility helper across MoviePy versions."""
    if hasattr(video_clip, "with_audio"):
        return video_clip.with_audio(audio_clip)  # MoviePy v2+
    return video_clip.set_audio(audio_clip)      # MoviePy v1


def merge_video_with_audio(
    video_path: str,
    audio_path: str,
    merged_path: str,
    video_volume: float = 1.0,
    audio_volume: float = 1.0,
) -> str:
    """
    Combines video with audio file, allowing volume control for both original audio and voiceover.
    Compatible with MoviePy v1 and v2.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(os.path.abspath(merged_path))
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Use a safe temp audio file in the system temp directory (Streamlit Cloud friendly)
    tmp_audiofile = os.path.join(tempfile.gettempdir(), "voxover_temp_audio.m4a")

    video_clip = VideoFileClip(video_path)
    added_audio_clip = AudioFileClip(audio_path)

    try:
        # Adjust volumes
        original_audio = video_clip.audio
        original_audio = _scale_volume(original_audio, video_volume)
        added_audio_clip = _scale_volume(added_audio_clip, audio_volume)

        # Trim added audio if longer than video
        if added_audio_clip.duration > video_clip.duration:
            added_audio_clip = _subclip(added_audio_clip, video_clip.duration)

        # Composite audio
        if original_audio is not None:
            final_audio = CompositeAudioClip([original_audio, added_audio_clip])
        else:
            final_audio = added_audio_clip

        final_clip = _set_audio(video_clip, final_audio)

        final_clip.write_videofile(
            merged_path,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=tmp_audiofile,
            remove_temp=True,
            logger=None,
        )

        return merged_path

    finally:
        # Close resources
        try:
            added_audio_clip.close()
        except Exception:
            pass
        try:
            video_clip.close()
        except Exception:
            pass
        try:
            final_clip.close()
        except Exception:
            pass
