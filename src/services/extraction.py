"""Serviço de extração de dados com LLM"""
import json
import logging
from datetime import datetime
from langchain_openai import ChatOpenAI
from ..config.settings import settings
from ..models.expense import ExpenseData, Tag

logger = logging.getLogger(__name__)

class ExtractionService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0,
            api_key=settings.openai_api_key
        )
    
    def extract(self, transcription: str) -> ExpenseData:
        """Extrai dados estruturados da transcrição"""
        try:
            logger.info("Extraindo informações da transcrição")
            
            today = datetime.now().strftime('%Y-%m-%d')
            prompt = self._build_prompt(transcription, today)
            
            response = self.llm.invoke(prompt)
            data = self._parse_response(response.content)
            
            # Converte para modelo
            expense = ExpenseData(
                description=data.get('description', 'Gasto'),
                date=data.get('date', today),
                amount_cents=data.get('amount_cents', -1000),
                notes=data.get('notes'),
                tags=[Tag(name=tag['name']) for tag in data.get('tags', [])]
            )
            
            logger.info(f"Dados extraídos: {expense}")
            return expense
        
        except Exception as e:
            logger.error(f"Erro na extração: {e}")
            raise
    
    def _build_prompt(self, text: str, today: str) -> str:
        return f"""
Você é um assistente que extrai informações de gastos de textos em português.

Data de hoje: {today}

Texto: "{text}"

Extraia as seguintes informações e retorne APENAS um JSON válido (sem markdown):

{{
    "description": "descrição curta do gasto (máximo 30 caracteres)",
    "notes": "observações adicionais",
    "date": "data no formato YYYY-MM-DD",
    "tags": [lista de tags como {{"name": "tag"}}],
    "amount_cents": valor em centavos negativo
}}

Regras:
- Se valor não mencionado, use -1000
- amount_cents NEGATIVO para despesa
- date formato YYYY-MM-DD
- tags relevantes ao contexto
"""
    
    def _parse_response(self, content: str) -> dict:
        # Remove markdown se presente
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
        
        return json.loads(content.strip())