import json

from utils.db import get_db_conn
from utils.logger import get_logger

logger = get_logger('analysis_repository')


class AnalysisRepository:
    @staticmethod
    async def ensure_table():
        async with get_db_conn() as conn:
            await conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS analysis_reports (
                    id SERIAL PRIMARY KEY,
                    code VARCHAR(20) NOT NULL,
                    stock_name VARCHAR(100),
                    period VARCHAR(20) NOT NULL,
                    kline_count INTEGER NOT NULL,
                    model_name VARCHAR(100) NOT NULL,
                    prompt_text TEXT NOT NULL,
                    input_payload JSONB NOT NULL,
                    analysis_markdown TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                '''
            )
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_analysis_reports_created_at ON analysis_reports(created_at DESC)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_analysis_reports_code ON analysis_reports(code)')

    @staticmethod
    async def create_report(
        *,
        code: str,
        stock_name: str,
        period: str,
        kline_count: int,
        model_name: str,
        prompt_text: str,
        input_payload: dict,
        analysis_markdown: str,
    ) -> int:
        await AnalysisRepository.ensure_table()
        async with get_db_conn() as conn:
            row = await conn.fetchrow(
                '''
                INSERT INTO analysis_reports (
                    code, stock_name, period, kline_count, model_name, prompt_text, input_payload, analysis_markdown
                ) VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8)
                RETURNING id
                ''',
                code,
                stock_name,
                period,
                kline_count,
                model_name,
                prompt_text,
                json.dumps(input_payload, ensure_ascii=False),
                analysis_markdown,
            )
            return row['id']

    @staticmethod
    async def list_reports(limit: int = 50) -> list[dict]:
        await AnalysisRepository.ensure_table()
        async with get_db_conn() as conn:
            rows = await conn.fetch(
                '''
                SELECT id, code, stock_name, period, kline_count, model_name, created_at
                FROM analysis_reports
                ORDER BY created_at DESC
                LIMIT $1
                ''',
                limit,
            )
            return [dict(row) for row in rows]

    @staticmethod
    async def get_report(report_id: int) -> dict | None:
        await AnalysisRepository.ensure_table()
        async with get_db_conn() as conn:
            row = await conn.fetchrow(
                '''
                SELECT id, code, stock_name, period, kline_count, model_name, prompt_text, input_payload, analysis_markdown, created_at
                FROM analysis_reports
                WHERE id = $1
                ''',
                report_id,
            )
            return dict(row) if row else None
