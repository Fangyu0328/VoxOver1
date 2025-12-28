# VoxOver: AI Narration Studio 🎙️🎬
Create AI voiceovers for videos — generate a script from the video + your instructions, synthesize speech in multiple voices, mix audio levels, and export a final narrated video.

# What this project does

VoxOver is a Streamlit app that helps you add AI narration to a video:
- Upload a video
- Describe the narration style you want
- Generate/edit the voiceover script
- Convert script → speech (multiple voice options)
- Mix volumes (original audio + voiceover)
- Merge and download the final video

## Features

- 🎬 **Video Analysis**: Automatically analyzes video content
- 🤖 **AI Text Generation**: Creates contextually relevant voiceover scripts
- 🗣️ **Text-to-Speech**: Converts text to natural-sounding speech with multiple voice options
- 🎚️ **Audio Mixing**: Control both original audio and voiceover volume levels
- 🎥 **Video Processing**: Merges the voiceover with your video

## Requirements

- Python 3.8+
- FFmpeg (required for video and audio processing)
- OpenAI API key

## Installation

### 1. Install FFmpeg

**Windows:**
1. Download FFmpeg from [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/) (release essentials package)
2. Extract to a location (e.g., `C:\FFmpeg`)
3. Add `C:\FFmpeg\bin` to your system PATH
4. Verify by running `ffmpeg -version` in a new command prompt

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

### 2. Clone the Repository

```bash
git clone https://github.com/Fangyu0328/VoxOver.git
cd VoxOver
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create Environment File

Create a `.env` file in the project root directory:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### 5. Create Temp Directory

```bash
mkdir temp
```

## Running the App

Start the Streamlit app:

```bash
streamlit run app.py
```

For automatic reloading when code changes (useful during development):

```bash
streamlit run app.py --server.runOnSave=true
```

The app will open in your default web browser at [http://localhost:8501](http://localhost:8501).

## How to Use

1. **Upload Video**: Upload a video file to start the process
2. **Enter Instructions**: Provide instructions for the style and content of the voiceover
3. **Generate Text**: Generate voiceover text based on video content and instructions
4. **Edit Text**: Review and edit the generated text if needed
5. **Choose Voice**: Select from different voice options 
6. **Generate Audio**: Create the voiceover audio
7. **Adjust Volume**: Control the volume levels of both original audio and voiceover
8. **Merge**: Combine the voiceover with your video
9. **Review**: Watch the final video with voiceover

## Project structure

- app.py — Streamlit UI + user workflow
- utils.py — core pipeline functions:
      - generate_voiceover_text(video_path, instructions)
      - generate_voiceover_audio(voiceover_text, file_path, voice_name='nova', speed=1.0)
      - merge_video_with_audio(video_path, audio_path, merged_path, video_volume=1.0, audio_volume=1.0)
- temp/ — temporary working directory (created locally)

## Deploying to Streamlit Cloud

1. Push your code to GitHub
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Connect your GitHub repository
4. Add your OpenAI API key as a secret in the Streamlit Cloud dashboard
5. Deploy the app

## Troubleshooting

- **FFmpeg Errors**: Ensure FFmpeg is correctly installed and in your PATH
- **API Key Issues**: Verify your OpenAI API key is correct in the `.env` file
- **Memory Errors**: Try processing smaller videos if you encounter memory issues
- **Missing Directory Errors**: Make sure the `temp` directory exists in the project root

## License

[MIT License](LICENSE)

## Acknowledgements

- This app uses OpenAI's API for text generation and speech synthesis
- Video processing is handled by MoviePy and FFmpeg

---

Created by [Fangyu Li] - Feel free to contribute or report issues!
