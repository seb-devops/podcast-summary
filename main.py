import argparse
from io import BytesIO
from typing import List
import openai
from pydub import AudioSegment
import yt_dlp



parser = argparse.ArgumentParser()
parser.add_argument("token")
parser.add_argument("youtube_url")
parser.add_argument("audience")
parser.add_argument("format")
args = parser.parse_args()

def speech_to_text(audio_segments):
    transcripts = []
    for segment in audio_segments:
        transcript= openai.Audio.transcribe("whisper-1", segment.export('wav'))
        transcripts.append(transcript['text'])
    return transcripts


def write_text_to_file(filename, texts):
    with open(filename, 'w') as f:
        for text in texts:
            f.write(text)
            f.write('\n')

def load_file(filename):
    with open(filename, "r") as file:
        return file.read()

def summarize_text(texts: List[str], audience: str, format: str):
    summaries = []
    for text in texts:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=f"Can you summarize this text from a {audience} standpoint in {format}: {text}",
            max_tokens= 2000
        )
        summary = response['choices'][0]['text']
        summaries.append(summary)

    return summaries

def validate_sense_of_whole_text(summaries):

    prompt_text = 'Can you make sure that those different summarized part of a whole text make sense togheter:'
    for summary in summaries:
        prompt_text += 'Part:'+ summary

    response = openai.Completion.create(
        model="text-davinci-003",
        
        prompt=prompt_text,
        max_tokens= 2000
    )
    
    return response['choices'][0]['text']

def segment_audio(filename):
    with open(filename, "rb") as file:
        chunked_audio = AudioSegment.from_mp3(file)
        # PyDub handles time in milliseconds
        ten_minutes = 10 * 60 * 1000
        chunks = []
        for i in range(0, len(chunked_audio), ten_minutes):
            chunks.append(chunked_audio[i:i+ten_minutes])
        return chunks

        
def download_audio_from_youtube(youtube_url: str):
    ydl_opts = {
        'outtmpl': '%(id)s',
        'format': 'mp3/bestaudio/best',
        # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
        'postprocessors': [{  # Extract audio using ffmpeg
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        error_code = ydl.download(youtube_url)
        return ''

def extract_info_from_youtube(youtube_url: str):
    ydl_opts = {}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)

    return f"{info['id']}.mp3"

def main():
    openai.api_key = args.token
    audience = args.audience
    format = args.format
    download_audio_from_youtube(args.youtube_url)
    filename = extract_info_from_youtube(args.youtube_url)
    audio = segment_audio(filename)
    
    transcript = speech_to_text(audio)
    write_text_to_file('transcript.md', transcript)
    
    summary = summarize_text(transcript,audience,format)
    write_text_to_file('summary.md', summary)
    print(validate_sense_of_whole_text(summary))

if __name__ == "__main__": 
    main()