"""Cliente da API Organizze"""
import logging
import requests
from typing import List, Optional
from ..config.settings import settings
from ..models.expense import ExpenseData, Category, Account, CreditCard

logger = logging.getLogger(__name__)

class OrganizzeClient:
    def __init__(self):
        self.base_url = settings.organizze_api_base
        self.auth = (settings.organizze_email, settings.organizze_token)
        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'OrganizzeTelegramBot/1.0'
        }
        
        # Cache de dados
        self._categories: Optional[List[Category]] = None
        self._accounts: Optional[List[Account]] = None
        self._credit_cards: Optional[List[CreditCard]] = None
    
    def get_categories(self, force_refresh: bool = False) -> List[Category]:
        """Obtém lista de categorias ativas"""
        if self._categories and not force_refresh:
            return self._categories
        
        try:
            logger.info("Buscando categorias do Organizze")
            
            url = f"{self.base_url}/categories"
            response = requests.get(url, auth=self.auth, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Filtra apenas categorias ativas
            active_categories = [
                Category(
                    id=cat['id'],
                    name=cat['name'],
                    kind=cat.get('kind', 'expense')
                )
                for cat in data
                if not cat.get('archived', False)
            ]
            
            self._categories = active_categories
            logger.info(f"Encontradas {len(active_categories)} categorias ativas")
            return active_categories
        
        except Exception as e:
            logger.error(f"Erro ao buscar categorias: {e}")
            return []
    
    def get_accounts(self, force_refresh: bool = False) -> List[Account]:
        """Obtém lista de contas ativas"""
        if self._accounts and not force_refresh:
            return self._accounts
        
        try:
            logger.info("Buscando contas do Organizze")
            
            url = f"{self.base_url}/accounts"
            response = requests.get(url, auth=self.auth, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Filtra apenas contas ativas
            active_accounts = [
                Account(
                    id=acc['id'],
                    name=acc['name'],
                    type=acc.get('type', 'checking')
                )
                for acc in data
                if not acc.get('archived', False)
            ]
            
            self._accounts = active_accounts
            logger.info(f"Encontradas {len(active_accounts)} contas ativas")
            return active_accounts
        
        except Exception as e:
            logger.error(f"Erro ao buscar contas: {e}")
            return []
    
    def get_credit_cards(self, force_refresh: bool = False) -> List[CreditCard]:
        """Obtém lista de cartões de crédito ativos"""
        if self._credit_cards and not force_refresh:
            return self._credit_cards
        
        try:
            logger.info("Buscando cartões de crédito do Organizze")
            
            url = f"{self.base_url}/credit_cards"
            response = requests.get(url, auth=self.auth, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Filtra apenas cartões ativos
            active_cards = [
                CreditCard(
                    id=card['id'],
                    name=card['name']
                )
                for card in data
                if not card.get('archived', False)
            ]
            
            self._credit_cards = active_cards
            logger.info(f"Encontrados {len(active_cards)} cartões ativos")
            return active_cards
        
        except Exception as e:
            logger.error(f"Erro ao buscar cartões: {e}")
            return []
    
    def find_category_by_name(self, category_name: str) -> Optional[Category]:
        """Busca categoria por nome (case-insensitive e parcial)"""
        categories = self.get_categories()
        category_lower = category_name.lower()
        
        # Busca exata
        for cat in categories:
            if cat.name.lower() == category_lower:
                return cat
        
        # Busca parcial
        for cat in categories:
            if category_lower in cat.name.lower() or cat.name.lower() in category_lower:
                return cat
        
        return None
    
    def find_account_by_name(self, account_name: str) -> Optional[Account]:
        """Busca conta por nome (case-insensitive e parcial)"""
        accounts = self.get_accounts()
        account_lower = account_name.lower()
        
        for acc in accounts:
            if account_lower in acc.name.lower() or acc.name.lower() in account_lower:
                return acc
        
        return None
    
    def find_credit_card_by_name(self, card_name: str) -> Optional[CreditCard]:
        """Busca cartão por nome (case-insensitive e parcial)"""
        cards = self.get_credit_cards()
        card_lower = card_name.lower()
        
        for card in cards:
            if card_lower in card.name.lower() or card.name.lower() in card_lower:
                return card
        
        return None
    
    def create_transaction(self, expense: ExpenseData) -> dict:
        """Cria uma transação no Organizze"""
        try:
            logger.info("Enviando transação para Organizze")
            
            url = f"{self.base_url}/transactions"
            payload = expense.to_organizze_payload()
            
            logger.debug(f"Payload: {payload}")
            
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