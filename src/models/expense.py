"""Modelos de dados"""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Tag:
    name: str

@dataclass
class ExpenseData:
    description: str
    date: str
    amount_cents: int
    notes: Optional[str] = None
    tags: Optional[List[Tag]] = None
    
    def to_organizze_payload(self) -> dict:
        payload = {
            "description": self.description,
            "date": self.date,
            "amount_cents": self.amount_cents,
        }
        
        if self.notes:
            payload["notes"] = self.notes
        
        if self.tags:
            payload["tags_attributes"] = [{"name": tag.name} for tag in self.tags]
        
        return payload