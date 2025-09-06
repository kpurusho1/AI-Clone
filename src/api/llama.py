import os
import httpx
import time
import urllib.parse
from typing import List, Dict, Any, Optional
from openai import OpenAI
from io import BytesIO
from llama_cloud_services import LlamaParse
from llama_index.readers.youtube_transcript.utils import is_youtube_video
from utils import extract_youtube_id
from youtube_transcript_api import YouTubeTranscriptApi

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize LlamaParse client
llama_parser = LlamaParse(
    api_key=LLAMAPARSE_API_KEY,  # can also be set in your env as LLAMA_CLOUD_API_KEY
    num_workers=4,       # if multiple files passed, split in `num_workers` API calls
    verbose=True,
    language="en"       # optionally define a language, default=en
)

def extract_youtube_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from various YouTube URL formats
    
    Args:
        url: YouTube URL in any format
        
    Returns:
        YouTube video ID or None if not a valid YouTube URL
    """
    import re
    # Regular expressions for different YouTube URL formats
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]+)',  # Standard and shortened URLs
        r'youtube\.com\/embed\/([\w-]+)',                      # Embed URLs
        r'youtube\.com\/v\/([\w-]+)',                          # Old embed URLs
        r'youtube\.com\/user\/[\w-]+\/\?v=([\w-]+)',         # User URLs
        r'youtube\.com\/attribution_link\?.*v%3D([\w-]+)',    # Attribution links
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def get_youtube_transcript(video_url: str):
    if not is_youtube_video(video_url):
        raise ValueError(f"Invalid YouTube URL: {video_url}")
    print(f"Getting transcript for YouTube video: {video_url}")
    
    try:
        # Extract video ID from URL
        video_id = extract_youtube_id(video_url)
        if not video_id:
            raise ValueError(f"Could not extract YouTube video ID from URL: {video_url}")
            
        print(f"Fetching transcript for YouTube video ID: {video_id}")
        
        # Get transcript using YouTubeTranscriptApi directly with the fetch method
        transcript_api = YouTubeTranscriptApi()
        fetched_transcript = transcript_api.fetch(video_id, languages=['en'])
        
        # Format transcript into a single text with timestamps
        full_transcript = ""
        for snippet in fetched_transcript.snippets:
            timestamp = snippet.start
            minutes = int(timestamp // 60)
            seconds = int(timestamp % 60)
            time_str = f"[{minutes:02d}:{seconds:02d}] "
            full_transcript += snippet.text + " "
        '''
        # Create a document object similar to what llama_index would return
        from llama_index.core.schema import Document
        document = Document(
            text=full_transcript,
            metadata={
                "source": video_url,
                "video_id": fetched_transcript.video_id,
                "language": fetched_transcript.language,
                "language_code": fetched_transcript.language_code,
                "is_generated": fetched_transcript.is_generated,
                "title": f"YouTube Transcript: {fetched_transcript.video_id}"
            }
        )
        '''
        print(f"Successfully retrieved transcript for YouTube video: {video_url}")
        return full_transcript
        
    except Exception as e:
        print(f"Error getting YouTube transcript: {str(e)}")
        raise Exception(f"Failed to retrieve YouTube transcript: {str(e)}")

def parse_document_url(document_url: str):
    try:
        # Parse document URL
        parsed_url = urllib.parse.urlparse(document_url)
        
        # Get document name from URL
        document_name = parsed_url.path.split('/')[-1]
        
        # Get document extension from URL
        document_extension = document_name.split('.')[-1]
        
        # Get document content from URL
        document_content = httpx.get(document_url).content
        
        # Parse document content
        document = llama_parser.parse(document_content, document_name, document_extension)
        
        # Return document
        return document
    except Exception as e:
        print(f"Error parsing document URL: {str(e)}")
        raise Exception(f"Failed to parse document URL: {str(e)}")