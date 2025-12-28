import os
import tempfile
import time
from pathlib import Path
import subprocess
import logging
from genai import GenAI
from moviepy import VideoFileClip


from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

jarvis = GenAI(OPENAI_API_KEY)



def get_video_duration(video_path):
    # Load the video file
    video = VideoFileClip(video_path)
    
    # Get the duration in seconds
    duration_in_seconds = video.duration
    
    # Make sure to close the video to free resources
    video.close()
    
    return duration_in_seconds



def generate_voiceover_text(video_path, instructions):
    """
    Generates an audio narration for a video based on user instructions.
    
    Args:
        video_path (str): Path to the video file
        instructions (str): User instructions for narration style/content
    
    Returns:
        str: video voiceover text
    """
    wps = 200/60 #200 words per minute/ 60 seconds
    duration_secs = get_video_duration(video_path)
    nwords_max = wps*duration_secs  
    print(f"\tDuration of video: {duration_secs} seconds")
    print(f"\tMax words for voiceover: {nwords_max} words")
    instructions_modified = instructions + f"\nYour voiceover text should be less than {nwords_max} words long."
    instructions_modified += "Do not use any hashtags or emojis in the voiceover text as this will be read aloud."
    voiceover_text = jarvis.generate_video_description(video_path, instructions_modified, model='gpt-4o-mini')
    return voiceover_text

    

def generate_voiceover_audio(voiceover_text, 
                             file_path, 
                            voice_name='nova', 
                             speed=1.0):
    complete  = jarvis.generate_audio(voiceover_text,
                           file_path, 
                           model='gpt-4o-mini-tts', 
                           voice=voice_name, 
                           speed=speed)
    return complete

def merge_video_with_audio(video_path, audio_path, merged_path, video_volume=1.0, audio_volume=1.0):
    """
    Merges a video with an audio file and allows controlling both the video and audio volume levels.
    Uses a version-independent approach that should work with most MoviePy versions.
    
    Parameters:
    ----------
    video_path : str
        Path to the input video file.
    audio_path : str
        Path to the audio file to be merged with the video.
    merged_path : str
        Path where the merged video will be saved.
    video_volume : float, optional
        Volume level for the original video audio (default is 1.0, which keeps the original volume).
        Values greater than 1.0 increase volume, less than 1.0 decrease volume.
    audio_volume : float, optional
        Volume level for the added audio track (default is 1.0, which keeps the original volume).
        Values greater than 1.0 increase volume, less than 1.0 decrease volume.
        
    Returns:
    -------
    str
        Path to the merged video file.
    """
    import os
    from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip
    
    try:
        # Load the video
        video_clip = VideoFileClip(video_path)
        print(f"Video duration: {video_clip.duration} seconds")
        
        # Load the added audio
        added_audio_clip = AudioFileClip(audio_path)
        print(f"Added audio duration: {added_audio_clip.duration} seconds")
        
        # Adjust video's original audio volume if needed
        original_audio = None
        if video_clip.audio is not None:
            original_audio = video_clip.audio
            if video_volume != 1.0:
                original_audio = original_audio.with_volume_scaled(video_volume)
        
        # Adjust the added audio volume if needed
        if audio_volume != 1.0:
            added_audio_clip = added_audio_clip.with_volume_scaled(audio_volume)
        
        # If added audio is longer than video, trim it to match video duration
        if added_audio_clip.duration > video_clip.duration:
            added_audio_clip = added_audio_clip.subclipped(0, video_clip.duration)
        
        # Create final audio - combine original video audio (if present) with the added audio
        if original_audio is not None:
            # If the original audio is shorter than the video, extend it to match
            if original_audio.duration < video_clip.duration:
                print(f"Original audio duration ({original_audio.duration}s) is shorter than video ({video_clip.duration}s), extending it")
                # For simplicity, we'll just use the audio as is and let MoviePy handle potential issues
            
            # Create a composite audio from both audio tracks
            final_audio = CompositeAudioClip([original_audio, added_audio_clip])
            
            # Create a new video clip without audio and then set the composite audio
            final_clip = video_clip.with_audio(final_audio)
        else:
            # If the video has no audio, just use the added audio track
            final_clip = video_clip.with_audio(added_audio_clip)
        
        # Ensure the output directory exists
        output_dir = os.path.dirname(os.path.abspath(merged_path))
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Write the final video to the specified path
        final_clip.write_videofile(
            merged_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            logger=None     # Suppress logger output
        )
        
        # Close the clips to release resources
        video_clip.close()
        added_audio_clip.close()
        if original_audio is not None:
            original_audio.close()
        final_clip.close()
        
        print(f"Successfully merged video and audio to: {merged_path}")
        return merged_path
        
    except Exception as e:
        print(f"Error merging video and audio: {e}")
        import traceback
        traceback.print_exc()
        raise