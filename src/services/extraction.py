"""Serviço de extração de dados com LLM"""
import json
import logging
from datetime import datetime
from langchain_openai import ChatOpenAI
from ..config.settings import settings
from ..models.expense import ExpenseData, Tag
from .organizze import OrganizzeClient

logger = logging.getLogger(__name__)

class ExtractionService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0,
            api_key=settings.openai_api_key
        )
        self.organizze_client = OrganizzeClient()
    
    def extract(self, transcription: str) -> ExpenseData:
        """Extrai dados estruturados da transcrição"""
        try:
            logger.info("Extraindo informações da transcrição")
            
            # Busca categorias, contas e cartões disponíveis
            categories = self.organizze_client.get_categories()
            accounts = self.organizze_client.get_accounts()
            credit_cards = self.organizze_client.get_credit_cards()
            
            today = datetime.now().strftime('%Y-%m-%d')
            prompt = self._build_prompt(transcription, today, categories, accounts, credit_cards)
            
            response = self.llm.invoke(prompt)
            data = self._parse_response(response.content)
            
            # Converte para modelo (não inclui tags, apenas a tag "Bot" será adicionada no payload)
            expense = ExpenseData(
                description=data.get('description', 'Gasto'),
                date=data.get('date', today),
                amount_cents=data.get('amount_cents', -1000),
                notes="Lançamento via Bot"
            )
            
            # Identifica categoria
            if data.get('category_name'):
                category = self.organizze_client.find_category_by_name(data['category_name'])
                if category:
                    expense.category_id = category.id
                    logger.info(f"Categoria identificada: {category.name} (ID: {category.id})")
            
            # Identifica conta ou cartão
            payment_method = data.get('payment_method', '').lower()
            
            if 'cartão' in payment_method or 'cartao' in payment_method or 'crédito' in payment_method or 'credito' in payment_method:
                # Tenta identificar qual cartão
                card_name = data.get('card_name', '')
                if card_name:
                    card = self.organizze_client.find_credit_card_by_name(card_name)
                    if card:
                        expense.credit_card_id = card.id
                        logger.info(f"Cartão identificado: {card.name} (ID: {card.id})")
                
                # Se não encontrou, usa o primeiro cartão disponível
                if not expense.credit_card_id and credit_cards:
                    expense.credit_card_id = credit_cards[0].id
                    logger.info(f"Usando cartão padrão: {credit_cards[0].name}")
            
            else:
                # Tenta identificar qual conta
                account_name = data.get('account_name', '')
                if account_name:
                    account = self.organizze_client.find_account_by_name(account_name)
                    if account:
                        expense.account_id = account.id
                        logger.info(f"Conta identificada: {account.name} (ID: {account.id})")
                
                # Se não encontrou, usa a primeira conta disponível
                if not expense.account_id and accounts:
                    expense.account_id = accounts[0].id
                    logger.info(f"Usando conta padrão: {accounts[0].name}")
            
            logger.info(f"Dados extraídos: {expense}")
            return expense
        
        except Exception as e:
            logger.error(f"Erro na extração: {e}")
            raise
    
    def _build_prompt(self, text: str, today: str, categories: list, accounts: list, credit_cards: list) -> str:
        # Formata listas para o prompt
        categories_str = "\n".join([f"- {cat.name} (ID: {cat.id}, tipo: {cat.kind})" for cat in categories[:20]])
        accounts_str = "\n".join([f"- {acc.name} (ID: {acc.id})" for acc in accounts])
        cards_str = "\n".join([f"- {card.name} (ID: {card.id})" for card in credit_cards])
        
        return f"""
Você é um assistente que extrai informações de gastos de textos em português.

Data de hoje: {today}

Texto: "{text}"

CATEGORIAS DISPONÍVEIS:
{categories_str}

CONTAS DISPONÍVEIS:
{accounts_str}

CARTÕES DE CRÉDITO DISPONÍVEIS:
{cards_str}

Extraia as seguintes informações e retorne APENAS um JSON válido (sem markdown):

{{
    "description": "descrição curta do gasto (máximo 30 caracteres)",
    "date": "data no formato YYYY-MM-DD",
    "amount_cents": valor em centavos negativo,
    "category_name": "nome da categoria mais apropriada da lista acima",
    "payment_method": "cartão de crédito" ou "conta corrente" ou "dinheiro",
    "card_name": "nome do cartão se mencionado",
    "account_name": "nome da conta se mencionada"
}}

Regras importantes:
- Se valor não mencionado, use -1000 (R$ 10,00)
- amount_cents SEMPRE NEGATIVO para despesa
- date formato YYYY-MM-DD (use data mencionada ou hoje)
- category_name deve ser uma das categorias da lista acima (escolha a mais apropriada)
- payment_method: identifique se foi mencionado cartão, conta ou dinheiro
- Se cartão mencionado, tente identificar qual na lista
- Se conta mencionada, tente identificar qual na lista
- NÃO inclua tags no JSON, elas serão adicionadas automaticamente
"""
    
    def _parse_response(self, content: str) -> dict:
        # Remove markdown se presente
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
        
        return json.loads(content.strip())