from dataclasses import dataclass
from datetime import datetime


@dataclass
class RecapRecord:
    id: int
    review_date: str
    stock_name: str
    stock_code: str | None
    take_profit: float | None
    stop_loss: float | None
    risk_reward_ratio: float | None
    is_success: bool
    failure_reason: str | None
    strategy_tag: str | None
    summary: str | None
    lessons_learned: str | None
    notes: str | None
    image_path: str | None
    created_at: datetime | None
    updated_at: datetime | None

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'review_date': self.review_date,
            'stock_name': self.stock_name,
            'stock_code': self.stock_code,
            'take_profit': self.take_profit,
            'stop_loss': self.stop_loss,
            'risk_reward_ratio': self.risk_reward_ratio,
            'is_success': self.is_success,
            'failure_reason': self.failure_reason,
            'strategy_tag': self.strategy_tag,
            'summary': self.summary,
            'lessons_learned': self.lessons_learned,
            'notes': self.notes,
            'image_path': self.image_path,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
        }
