import calendar
from datetime import datetime, timedelta, timezone

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np


def float_hours_to_hm(hours_float: float | np.float32) -> str:
    td = timedelta(hours=hours_float)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"


def get_declination_spencer(day_of_year: int) -> float:
    """Формула Спенсера"""
    beta = np.radians(360 * (day_of_year - 1) / 365)
    return (180 / np.pi) * (
            0.006918
            - 0.399912 * np.cos(beta) + 0.070257 * np.sin(beta)
            - 0.006758 * np.cos(2 * beta) + 0.00907 * np.sin(2 * beta)
            - 0.002697 * np.cos(3 * beta) + 0.00148 * np.sin(3 * beta)
    )


def get_declination_kuper(day_of_year: int) -> float:
    """Формула Купера"""
    return 23.45 * np.sin(np.radians(360 * (284 + day_of_year) / 365))


def calculate_daylight_hours(day_of_year: int, latitude: float) -> float:
    # Расчёт склонения
    declination = get_declination_spencer(day_of_year)

    # Преобразуем в радианы
    lat_rad = np.radians(latitude)
    dec_rad = np.radians(declination)

    # Учет атмосферной рефракции (стандартная поправка -0.83°)
    # Для практических расчетов часто используют -0.8333°
    refraction_correction = np.radians(0.8333)

    # Защита от нулей
    test_cos = np.cos(lat_rad) * np.cos(dec_rad)
    if abs(test_cos) < 1e-10:
        return 24.0 if np.sin(lat_rad) * np.sin(dec_rad) > 0 else 0.0

    # Вычисляем часовой угол с учетом рефракции
    cos_h = -np.tan(lat_rad) * np.tan(dec_rad) - np.sin(refraction_correction) / (np.cos(lat_rad) * np.cos(dec_rad))

    if cos_h >= 1:
        return 0.0  # Полярная ночь
    if cos_h <= -1:
        return 24.0  # Полярный день

    # Ограничиваем значение
    cos_h = np.clip(cos_h, -1.0, 1.0)

    # Продолжительность дня в часах
    h = np.degrees(np.arccos(cos_h))
    daylight = 2 * h / 15.0

    return daylight


def plot_daylight_duration(latitude, year=None, show_solstices=True, tz=None, city_name=''):
    """
    Строит график продолжительности светового дня в течение года.

    Параметры:
    latitude (float): географическая широта в градусах
    year (int): год для отображения дат (по умолчанию текущий)
    show_solstices (bool): показывать ли солнцестояния и равноденствия
    """

    # Создаем график
    fig, ax = plt.subplots(figsize=(12, 6))

    # Устанавливаем год
    if year is None:
        year = datetime.now(tz=tz).year

    # Проверяем високосный ли год
    days_in_year = 366 if calendar.isleap(year) else 365

    # Создаем массивы данных

    freq = 30  # Points per day

    days = list(np.arange(1, days_in_year + 1, 1 / freq))
    daylight_hours = np.array([calculate_daylight_hours(day, latitude) for day in days])

    # Создаем даты для оси X
    dates_ticks = [datetime(year, 1, 1) + timedelta(seconds=int(86400 * day - 86400)) for day in days]

    # Рисуем основной график
    ax.plot(dates_ticks, daylight_hours, 'b-', linewidth=2, label='Длина дня')
    ax.fill_between(dates_ticks, 0, daylight_hours, alpha=0.3, color='skyblue')

    # Скорость изменения длины дня
    ax2 = ax.twinx()
    ax.set_zorder(ax2.get_zorder() + 1)
    ax.patch.set_visible(False)
    daylight_derivative = np.gradient(daylight_hours, edge_order=1) * 60
    ax2.plot(dates_ticks, daylight_derivative, 'g-', linewidth=2, label='Изменение')
    y_diff = np.max([np.abs(np.max(daylight_derivative)), np.abs(np.min(daylight_derivative))])
    y_min, y_max = -y_diff, y_diff
    ax2.set_ylim(y_min, y_max)
    ax2.set_yticks(np.arange(y_min, y_max + 0.00000000001, y_diff / 5))
    ax2.spines['right'].set_color('green')
    ax2.set_ylabel('Изменение (минуты)', fontsize=12, color='green')
    ax2.tick_params(axis='y', colors='green', right=False)

    # Настройки графика
    ax.set_ylabel('Продолжительность дня (часы)', fontsize=12)
    ax.set_title('Продолжительность светового дня в течение года', fontsize=14, fontweight='bold')

    # Настройка оси X (даты)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax.xaxis.set_minor_locator(mdates.WeekdayLocator())

    # Настройка оси Y
    ax.set_ylim(0, 24)
    ax.set_yticks(np.arange(0, 25, 2))
    ax.grid(True, alpha=0.5, linestyle='--')

    # Линия для 12 часов
    ax.axhline(y=12, color='gray', linestyle=':', alpha=0.9, label='12 часов')

    # Добавляем информацию о солнцестояниях и равноденствиях
    if show_solstices:
        # Даты солнцестояний и равноденствий (приблизительно)
        events = {
            'Весеннее равноденствие': datetime(year, 3, 20),
            'Летнее солнцестояние': datetime(year, 6, 24),
            'Осеннее равноденствие': datetime(year, 9, 22),
            'Зимнее солнцестояние': datetime(year, 12, 21),
            'Сегодня': datetime(year, datetime.now(tz=tz).month, datetime.now(tz=tz).day)
        }

        for event_name, event_date in events.items():
            # Находим ближайший день в массиве
            idx = min(range(len(dates_ticks)), key=lambda i: abs((dates_ticks[i] - event_date).days))
            hours = float(daylight_hours[idx])
            # hours_str = f'{int(hours)}:{int((hours - int(hours)) * 60)}'
            hours_str = float_hours_to_hm(hours)

            # Добавляем вертикальную линию и текст
            if event_name == 'Сегодня':
                event_name = 'Сегодня\n' + datetime.strftime(event_date, '%d.%m.%Y')
                color = 'red'
                dot_color = 'ro'
                line_style = '-'
                y_cor = hours + 0.5
            else:
                color = 'blue'
                dot_color = 'bo'
                line_style = '--'
                y_cor = 1

            ax.axvline(event_date, color=color, linestyle=line_style, alpha=0.5) # noqa
            ax.plot(event_date, hours, dot_color, markersize=8) # noqa
            ax.text(event_date, y_cor, f'{event_name}\n{hours_str}', # noqa
                    ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

    # Добавляем статистику в легенду
    stats_text = (f'{city_name}'
                  f'Широта: {latitude}°\n'
                  f'Min: {float_hours_to_hm(np.min(daylight_hours))}\n'
                  f'Avg: {float_hours_to_hm(np.mean(daylight_hours))}\n'
                  f'Max: {float_hours_to_hm(np.max(daylight_hours))}')
    ax.text(0.99, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
            horizontalalignment='right', verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2, loc='upper left', fontsize=10)
    plt.xlim(datetime(year, 1, 1), datetime(year, 12, 31))
    return fig, ax


# Пример использования:
if __name__ == "__main__":
    fig, ax = plot_daylight_duration(city_name='Москва\n', latitude=55.66459, tz=timezone(timedelta(hours=3)))

    filename = "daylight_duration.png"
    fig.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Plot saved as '{filename}'")
