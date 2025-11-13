"""Cliente da API Organizze"""
import logging
import requests
from ..config.settings import settings
from ..models.expense import ExpenseData

logger = logging.getLogger(__name__)

class OrganizzeClient:
    def __init__(self):
        self.base_url = settings.organizze_api_base
        self.auth = (settings.organizze_email, settings.organizze_token)
        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'OrganizzeTelegramBot/1.0'
        }
    
    def create_transaction(self, expense: ExpenseData) -> dict:
        """Cria uma transação no Organizze"""
        try:
            logger.info("Enviando transação para Organizze")
            
            url = f"{self.base_url}/transactions"
            payload = expense.to_organizze_payload()
            
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Transação criada: ID {result.get('id')}")
            return result
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erro HTTP: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Erro ao criar transação: {e}")
            raise