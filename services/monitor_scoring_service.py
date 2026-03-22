from typing import Any


class MonitorScoringService:
    """监控股评分服务。"""

    @staticmethod
    def _price_gap_ratio(current_price: float | None, target_price: float | None) -> float:
        if not current_price or not target_price:
            return 0.0
        return (target_price - current_price) / target_price

    @staticmethod
    def score_stock(stock: dict[str, Any], holding_codes: set[str]) -> dict[str, Any]:
        score = 0
        reason_tags: list[str] = []

        valuation_status = stock.get('valuation_status', '未知')
        technical_status = stock.get('technical_status', '无信号')
        trend = stock.get('trend', '未知')
        current_price = stock.get('current_price')
        reasonable_price_min = stock.get('reasonable_price_min')
        reasonable_price_max = stock.get('reasonable_price_max')
        code = stock.get('code')
        is_holding = code in holding_codes

        if valuation_status == '低估':
            score += 35
            reason_tags.append('低估')
        elif valuation_status == '正常':
            score += 20
        elif valuation_status == '高估':
            score += 5
            reason_tags.append('高估')
        else:
            score += 10

        discount_ratio = MonitorScoringService._price_gap_ratio(current_price, reasonable_price_min)
        if discount_ratio > 0:
            score += min(5, round(discount_ratio * 50))

        if technical_status == '加仓':
            score += 30
            reason_tags.append('接近关键均线')
        elif technical_status == '无信号':
            score += 15
        else:
            reason_tags.append('破位')

        if trend == '多头':
            score += 20
            reason_tags.append('多头')
        elif trend == '震荡':
            score += 10
        elif trend == '未知':
            score += 5

        if is_holding:
            score += 10
            reason_tags.append('持仓股')
            if technical_status == '加仓':
                score += 5

        risk_level = 'low'
        if technical_status == '破位' or (valuation_status == '高估' and trend == '空头'):
            risk_level = 'high'
        elif trend == '空头' or valuation_status == '高估':
            risk_level = 'medium'

        action_label = '观察'
        if risk_level == 'high':
            action_label = '风险'
        elif valuation_status == '高估':
            action_label = '高估谨慎'
        elif valuation_status == '低估' and technical_status == '加仓':
            action_label = '可分批'
        elif technical_status == '加仓' or (valuation_status in {'低估', '正常'} and trend != '空头'):
            action_label = '接近买点'

        is_buy_candidate = action_label in {'接近买点', '可分批'}
        is_risk_stock = risk_level in {'medium', 'high'}
        is_focus = (score >= 60 and risk_level != 'high') or is_holding

        if reasonable_price_max and current_price and current_price > reasonable_price_max:
            reason_tags.append('高于合理区间')

        stock.update(
            {
                'score': max(0, min(100, int(score))),
                'action_label': action_label,
                'risk_level': risk_level,
                'is_holding': is_holding,
                'is_focus': is_focus,
                'is_buy_candidate': is_buy_candidate,
                'is_risk_stock': is_risk_stock,
                'reason_tags': reason_tags[:4],
            }
        )
        return stock
