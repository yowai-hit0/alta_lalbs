from google.cloud import speech
from google.cloud.exceptions import GoogleCloudError
from typing import Optional, Tuple
import os
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class SpeechToTextService:
    """Service for Google Speech-to-Text processing"""
    
    def __init__(self):
        self.client = None
        self._available = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize client with error handling"""
        try:
            # Check if Google Cloud credentials are available
            if not settings.gcs_project_id:
                logger.warning("Speech-to-Text not configured: Missing GCS project ID")
                self._available = False
                return
            
            # Check if credentials file exists
            if settings.google_application_credentials and not os.path.exists(settings.google_application_credentials):
                logger.warning(f"Speech-to-Text not available: Credentials file not found at {settings.google_application_credentials}")
                self._available = False
                return
            
            # Initialize client
            self.client = speech.SpeechClient()
            self._available = True
            logger.info("Speech-to-Text service is available and configured")
            
        except Exception as e:
            logger.warning(f"Speech-to-Text not available: {str(e)}")
            self._available = False
    
    def is_available(self) -> bool:
        """Check if Speech-to-Text service is available"""
        return self._available is True
    
    def transcribe_audio(self, gcs_uri: str, language_code: str = "en-US") -> Tuple[Optional[str], Optional[int]]:
        """
        Transcribe audio using Google Speech-to-Text
        
        Args:
            gcs_uri: GCS URI of the audio file to transcribe
            language_code: Language code for transcription (default: en-US)
            
        Returns:
            Tuple of (transcription_text, duration_seconds) or (None, None) if failed
        """
        if not self.is_available():
            logger.warning("Speech-to-Text service is not available. Cannot transcribe audio.")
            return None, None
        
        try:
            # Validate GCS URI
            if not gcs_uri.startswith('gs://'):
                logger.error(f"Invalid GCS URI: {gcs_uri}")
                return None, None
            
            # Configure audio
            audio = speech.RecognitionAudio(uri=gcs_uri)
            
            # Configure recognition
            config = speech.RecognitionConfig(
                encoding=self._get_encoding(gcs_uri),
                sample_rate_hertz=self._get_sample_rate(gcs_uri),
                language_code=language_code,
                enable_automatic_punctuation=True,
                enable_word_time_offsets=True,
            )
            
            # Perform transcription
            response = self.client.recognize(config=config, audio=audio)
            
            # Extract results
            if response.results:
                # Combine all alternatives
                transcript = ""
                for result in response.results:
                    transcript += result.alternatives[0].transcript + " "
                
                # Calculate duration (approximate)
                duration = self._estimate_duration(gcs_uri)
                
                logger.info(f"Successfully transcribed audio: {gcs_uri}")
                return transcript.strip(), duration
            
            logger.warning(f"No transcription results for audio: {gcs_uri}")
            return None, None
            
        except GoogleCloudError as e:
            logger.error(f"Speech-to-Text processing failed: {str(e)}")
            return None, None
        except Exception as e:
            logger.error(f"Unexpected error during Speech-to-Text processing: {str(e)}")
            return None, None
    
    def _get_encoding(self, gcs_uri: str) -> speech.RecognitionConfig.AudioEncoding:
        """Get audio encoding based on file extension"""
        ext = gcs_uri.lower().split('.')[-1]
        encoding_map = {
            'wav': speech.RecognitionConfig.AudioEncoding.LINEAR16,
            'flac': speech.RecognitionConfig.AudioEncoding.FLAC,
            'mp3': speech.RecognitionConfig.AudioEncoding.MP3,
            'ogg': speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
            'aac': speech.RecognitionConfig.AudioEncoding.AAC,
        }
        return encoding_map.get(ext, speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED)
    
    def _get_sample_rate(self, gcs_uri: str) -> int:
        """Get sample rate based on file type"""
        ext = gcs_uri.lower().split('.')[-1]
        # Default sample rates for common formats
        sample_rates = {
            'wav': 44100,
            'flac': 44100,
            'mp3': 44100,
            'ogg': 48000,
            'aac': 44100,
        }
        return sample_rates.get(ext, 44100)
    
    def _estimate_duration(self, gcs_uri: str) -> Optional[int]:
        """Estimate audio duration (placeholder implementation)"""
        # In a real implementation, you would:
        # 1. Download the file from GCS
        # 2. Use a library like librosa or pydub to get duration
        # 3. Return the actual duration in seconds
        
        # For now, return a placeholder
        return 120  # 2 minutes placeholder


# Global instance
speech_to_text_service = SpeechToTextService()
