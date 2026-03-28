from datetime import datetime

from models.recap import RecapRecord
from utils.db import get_db_conn
from utils.logger import get_logger

logger = get_logger('recap_repository')


class RecapRepository:
    @staticmethod
    async def ensure_table() -> None:
        async with get_db_conn() as conn:
            await conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS trade_recaps (
                    id SERIAL PRIMARY KEY,
                    review_date TIMESTAMP NOT NULL,
                    stock_name VARCHAR(100) NOT NULL,
                    stock_code VARCHAR(20),
                    take_profit NUMERIC(12, 4),
                    stop_loss NUMERIC(12, 4),
                    risk_reward_ratio NUMERIC(12, 4),
                    profit_amount NUMERIC(14, 2),
                    is_success BOOLEAN NOT NULL DEFAULT FALSE,
                    failure_reason TEXT,
                    strategy_tag VARCHAR(100),
                    summary TEXT,
                    lessons_learned TEXT,
                    notes TEXT,
                    image_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                '''
            )
            await conn.execute('ALTER TABLE trade_recaps ADD COLUMN IF NOT EXISTS profit_amount NUMERIC(14, 2)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_trade_recaps_review_date ON trade_recaps(review_date DESC)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_trade_recaps_stock_code ON trade_recaps(stock_code)')

    @staticmethod
    def _build_model(row) -> RecapRecord:
        return RecapRecord(
            id=row['id'],
            review_date=row['review_date'].strftime('%Y-%m-%d %H:%M:%S'),
            stock_name=row['stock_name'],
            stock_code=row['stock_code'],
            take_profit=float(row['take_profit']) if row['take_profit'] is not None else None,
            stop_loss=float(row['stop_loss']) if row['stop_loss'] is not None else None,
            risk_reward_ratio=float(row['risk_reward_ratio']) if row['risk_reward_ratio'] is not None else None,
            profit_amount=float(row['profit_amount']) if row['profit_amount'] is not None else None,
            is_success=row['is_success'],
            failure_reason=row['failure_reason'],
            summary=row['summary'],
            lessons_learned=row['lessons_learned'],
            image_path=row['image_path'],
            strategy_tag=row['strategy_tag'],
            notes=row['notes'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

    @staticmethod
    async def list_records(limit: int = 100) -> list[RecapRecord]:
        await RecapRepository.ensure_table()
        async with get_db_conn() as conn:
            rows = await conn.fetch(
                '''
                SELECT *
                FROM trade_recaps
                ORDER BY review_date DESC, id DESC
                LIMIT $1
                ''',
                limit,
            )
            return [RecapRepository._build_model(row) for row in rows]

    @staticmethod
    async def get_record(record_id: int) -> RecapRecord | None:
        await RecapRepository.ensure_table()
        async with get_db_conn() as conn:
            row = await conn.fetchrow(
                '''
                SELECT *
                FROM trade_recaps
                WHERE id = $1
                ''',
                record_id,
            )
            return RecapRepository._build_model(row) if row else None

    @staticmethod
    async def create_record(
        *,
        review_date: datetime,
        stock_name: str,
        stock_code: str | None,
        take_profit: float | None,
        stop_loss: float | None,
        risk_reward_ratio: float | None,
        profit_amount: float | None,
        is_success: bool,
        failure_reason: str | None,
        strategy_tag: str | None,
        summary: str | None,
        lessons_learned: str | None,
        notes: str | None,
        image_path: str | None,
    ) -> int:
        await RecapRepository.ensure_table()
        async with get_db_conn() as conn:
            row = await conn.fetchrow(
                '''
                INSERT INTO trade_recaps (
                    review_date, stock_name, stock_code, take_profit, stop_loss, risk_reward_ratio,
                    profit_amount, is_success, failure_reason, strategy_tag, summary, lessons_learned, notes, image_path
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                RETURNING id
                ''',
                review_date,
                stock_name,
                stock_code,
                take_profit,
                stop_loss,
                risk_reward_ratio,
                profit_amount,
                is_success,
                failure_reason,
                strategy_tag,
                summary,
                lessons_learned,
                notes,
                image_path,
            )
            return row['id']

    @staticmethod
    async def update_record(
        *,
        record_id: int,
        review_date: datetime,
        stock_name: str,
        stock_code: str | None,
        take_profit: float | None,
        stop_loss: float | None,
        risk_reward_ratio: float | None,
        profit_amount: float | None,
        is_success: bool,
        failure_reason: str | None,
        strategy_tag: str | None,
        summary: str | None,
        lessons_learned: str | None,
        notes: str | None,
        image_path: str | None,
    ) -> bool:
        await RecapRepository.ensure_table()
        async with get_db_conn() as conn:
            result = await conn.execute(
                '''
                UPDATE trade_recaps
                SET review_date = $1,
                    stock_name = $2,
                    stock_code = $3,
                    take_profit = $4,
                    stop_loss = $5,
                    risk_reward_ratio = $6,
                    profit_amount = $7,
                    is_success = $8,
                    failure_reason = $9,
                    strategy_tag = $10,
                    summary = $11,
                    lessons_learned = $12,
                    notes = $13,
                    image_path = $14,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $15
                ''',
                review_date,
                stock_name,
                stock_code,
                take_profit,
                stop_loss,
                risk_reward_ratio,
                profit_amount,
                is_success,
                failure_reason,
                strategy_tag,
                summary,
                lessons_learned,
                notes,
                image_path,
                record_id,
            )
            return result.endswith('1')

    @staticmethod
    async def delete_record(record_id: int) -> bool:
        await RecapRepository.ensure_table()
        async with get_db_conn() as conn:
            result = await conn.execute('DELETE FROM trade_recaps WHERE id = $1', record_id)
            return result.endswith('1')
