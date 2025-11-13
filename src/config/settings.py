"""Configurações do projeto"""
import os
from dataclasses import dataclass

@dataclass
class Settings:
    # Telegram
    telegram_bot_token: str
    
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    whisper_model: str = "whisper-1"
    
    # Organizze
    organizze_email: str
    organizze_token: str
    organizze_api_base: str = "https://api.organizze.com.br/rest/v2"
    
    # Diretórios
    audio_dir: str = "data/audios"
    
    @classmethod
    def from_env(cls):
        return cls(
            telegram_bot_token=os.getenv('TELEGRAM_BOT_TOKEN', ''),
            openai_api_key=os.getenv('OPENAI_API_KEY', ''),
            organizze_email=os.getenv('ORGANIZZE_EMAIL', ''),
            organizze_token=os.getenv('ORGANIZZE_TOKEN', ''),
        )
    
    def validate(self):
        required = [
            self.telegram_bot_token,
            self.openai_api_key,
            self.organizze_email,
            self.organizze_token
        ]
        if not all(required):
            raise ValueError("Todas as variáveis de ambiente são obrigatórias!")

settings = Settings.from_env()