"""Serviço de transcrição de áudio"""
import logging
from openai import OpenAI
from ..config.settings import settings

logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    def transcribe(self, audio_path: str) -> str:
        """Transcreve áudio usando Whisper"""
        try:
            logger.info(f"Transcrevendo áudio: {audio_path}")
            
            with open(audio_path, 'rb') as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    model=settings.whisper_model,
                    file=audio_file,
                    language="pt"
                )
            
            logger.info(f"Transcrição concluída: {transcription.text}")
            return transcription.text
        
        except Exception as e:
            logger.error(f"Erro na transcrição: {e}")
            raise