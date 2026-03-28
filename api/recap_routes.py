from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from repositories.recap_repository import RecapRepository
from utils.api_helpers import current_timestamp, success_response
from utils.logger import get_logger

logger = get_logger('recap_routes')
recap_router = APIRouter()

UPLOAD_DIR = Path('static/uploads/recaps')


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _parse_float(value: str | None) -> float | None:
    cleaned = _normalize_text(value)
    return float(cleaned) if cleaned is not None else None


def _parse_datetime(value: str) -> datetime:
    for fmt in ('%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise HTTPException(status_code=400, detail='时间格式不正确')


async def _save_image(image: UploadFile | None) -> str | None:
    if image is None or not image.filename:
        return None
    suffix = Path(image.filename).suffix.lower()
    if suffix not in {'.png', '.jpg', '.jpeg', '.webp', '.gif'}:
        raise HTTPException(status_code=400, detail='仅支持 png/jpg/jpeg/webp/gif 图片')
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f'{uuid4().hex}{suffix}'
    target_path = UPLOAD_DIR / filename
    content = await image.read()
    target_path.write_bytes(content)
    return f'/static/uploads/recaps/{filename}'


def _delete_image(image_path: str | None) -> None:
    if not image_path:
        return
    local_path = Path(image_path.lstrip('/'))
    if local_path.exists():
        local_path.unlink()


@recap_router.get('')
async def list_recaps():
    logger.info('GET /api/recaps')
    records = await RecapRepository.list_records()
    return success_response(timestamp=current_timestamp(), data={'records': [item.to_dict() for item in records]})


@recap_router.get('/{record_id}')
async def get_recap(record_id: int):
    logger.info(f'GET /api/recaps/{record_id}')
    record = await RecapRepository.get_record(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail='复盘记录不存在')
    return success_response(timestamp=current_timestamp(), data={'record': record.to_dict()})


@recap_router.post('')
async def create_recap(
    review_date: str = Form(...),
    stock_name: str = Form(...),
    stock_code: str | None = Form(None),
    take_profit: str | None = Form(None),
    stop_loss: str | None = Form(None),
    risk_reward_ratio: str | None = Form(None),
    profit_amount: str | None = Form(None),
    is_success: str = Form('false'),
    failure_reason: str | None = Form(None),
    strategy_tag: str | None = Form(None),
    summary: str | None = Form(None),
    lessons_learned: str | None = Form(None),
    notes: str | None = Form(None),
    image: UploadFile | None = File(None),
):
    logger.info(f'POST /api/recaps {stock_name}')
    image_path = await _save_image(image)
    record_id = await RecapRepository.create_record(
        review_date=_parse_datetime(review_date),
        stock_name=stock_name.strip(),
        stock_code=_normalize_text(stock_code),
        take_profit=_parse_float(take_profit),
        stop_loss=_parse_float(stop_loss),
        risk_reward_ratio=_parse_float(risk_reward_ratio),
        profit_amount=_parse_float(profit_amount),
        is_success=is_success.lower() == 'true',
        failure_reason=_normalize_text(failure_reason),
        strategy_tag=_normalize_text(strategy_tag),
        summary=_normalize_text(summary),
        lessons_learned=_normalize_text(lessons_learned),
        notes=_normalize_text(notes),
        image_path=image_path,
    )
    return success_response(timestamp=current_timestamp(), data={'id': record_id, 'image_path': image_path})


@recap_router.put('/{record_id}')
async def update_recap(
    record_id: int,
    review_date: str = Form(...),
    stock_name: str = Form(...),
    stock_code: str | None = Form(None),
    take_profit: str | None = Form(None),
    stop_loss: str | None = Form(None),
    risk_reward_ratio: str | None = Form(None),
    profit_amount: str | None = Form(None),
    is_success: str = Form('false'),
    failure_reason: str | None = Form(None),
    strategy_tag: str | None = Form(None),
    summary: str | None = Form(None),
    lessons_learned: str | None = Form(None),
    notes: str | None = Form(None),
    keep_existing_image: str = Form('true'),
    image: UploadFile | None = File(None),
):
    logger.info(f'PUT /api/recaps/{record_id}')
    existing = await RecapRepository.get_record(record_id)
    if existing is None:
        raise HTTPException(status_code=404, detail='复盘记录不存在')

    image_path = existing.image_path
    new_image_path = await _save_image(image)
    if new_image_path:
        _delete_image(existing.image_path)
        image_path = new_image_path
    elif keep_existing_image.lower() != 'true':
        _delete_image(existing.image_path)
        image_path = None

    updated = await RecapRepository.update_record(
        record_id=record_id,
        review_date=_parse_datetime(review_date),
        stock_name=stock_name.strip(),
        stock_code=_normalize_text(stock_code),
        take_profit=_parse_float(take_profit),
        stop_loss=_parse_float(stop_loss),
        risk_reward_ratio=_parse_float(risk_reward_ratio),
        profit_amount=_parse_float(profit_amount),
        is_success=is_success.lower() == 'true',
        failure_reason=_normalize_text(failure_reason),
        strategy_tag=_normalize_text(strategy_tag),
        summary=_normalize_text(summary),
        lessons_learned=_normalize_text(lessons_learned),
        notes=_normalize_text(notes),
        image_path=image_path,
    )
    if not updated:
        raise HTTPException(status_code=404, detail='复盘记录不存在')
    return success_response(timestamp=current_timestamp(), data={'id': record_id, 'image_path': image_path})


@recap_router.delete('/{record_id}')
async def delete_recap(record_id: int):
    logger.info(f'DELETE /api/recaps/{record_id}')
    existing = await RecapRepository.get_record(record_id)
    if existing is None:
        raise HTTPException(status_code=404, detail='复盘记录不存在')
    deleted = await RecapRepository.delete_record(record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail='复盘记录不存在')
    _delete_image(existing.image_path)
    return success_response(timestamp=current_timestamp(), message='复盘记录已删除')
