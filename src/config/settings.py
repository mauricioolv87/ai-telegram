"""Configurações do projeto"""
import os
from dataclasses import dataclass
from typing import Optional


# Tenta carregar um arquivo .env na raiz do projeto. Primeiro tenta usar python-dotenv
# se estiver instalado; caso contrário faz um parser simples para popular os.environ.
def _load_dotenv_if_exists():
    # calcula a raiz do projeto (duas pastas acima deste arquivo: src/config -> project root)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    env_path = os.path.join(project_root, '.env')

    if not os.path.exists(env_path):
        return

    try:
        # se python-dotenv estiver disponível, use-o (preserva comportamento esperado)
        from dotenv import load_dotenv
        load_dotenv(env_path)
        return
    except Exception:
        # fallback simples: lê linhas KEY=VALUE e popula os.environ somente se não existir
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' not in line:
                        continue
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip()
                    # remove aspas simples/duplas ao redor se houver
                    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                    # só define se ainda não estiver definido no ambiente
                    os.environ.setdefault(key, val)
        except Exception:
            # em caso de qualquer erro, não bloqueia — as variáveis podem vir de outro lugar
            return


# Carrega .env automaticamente
_load_dotenv_if_exists()

@dataclass
class Settings:
    # Telegram
    telegram_bot_token: str
    
    # OpenAI
    openai_api_key: str

    # Organizze (sem default — devem ficar antes dos campos com default)
    organizze_email: str
    organizze_token: str

    # Campos com default
    openai_model: str = "gpt-4o-mini"
    whisper_model: str = "whisper-1"
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