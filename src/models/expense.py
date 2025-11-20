"""Modelos de dados"""
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Tag:
    name: str

@dataclass
class Category:
    id: int
    name: str
    kind: str  # 'expense' ou 'revenue'

@dataclass
class Account:
    id: int
    name: str
    type: str  # 'checking' ou 'savings'

@dataclass
class CreditCard:
    id: int
    name: str

@dataclass
class ExpenseData:
    description: str
    date: str
    amount_cents: int
    notes: str = "Lançamento via Bot"
    category_id: Optional[int] = None
    account_id: Optional[int] = None
    credit_card_id: Optional[int] = None
    
    def to_organizze_payload(self) -> dict:
        payload = {
            "description": self.description,
            "date": self.date,
            "amount_cents": self.amount_cents,
            "notes": self.notes,
            "tags": [{"name": "Bot"}]  # Sempre envia apenas a tag "Bot"
        }
        
        # Adiciona categoria se disponível
        if self.category_id:
            payload["category_id"] = self.category_id
        
        # Adiciona conta ou cartão (mutuamente exclusivos)
        if self.credit_card_id:
            payload["credit_card_id"] = self.credit_card_id
        elif self.account_id:
            payload["account_id"] = self.account_id
        
        return payload