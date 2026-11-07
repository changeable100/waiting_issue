"""真实留出集到位后由论文成员调用，不随附虚构精度。"""
from .model import number


def evaluate(rows):
    """每行 actual_min/predicted_min/lower_min/upper_min，必须同一等待口径。"""
    if not rows:
        raise ValueError('验证集不能为空')
    errors = []
    covered = 0
    for row in rows:
        for key in ('actual_min', 'predicted_min', 'lower_min', 'upper_min'):
            number(row[key], key)
        if row['lower_min'] > row['upper_min']:
            raise ValueError('区间上下界颠倒')
        errors.append(abs(row['actual_min'] - row['predicted_min']))
        covered += row['lower_min'] <= row['actual_min'] <= row['upper_min']
    return {'n': len(rows), 'mae_min': sum(errors) / len(rows),
            'interval_coverage': covered / len(rows)}
