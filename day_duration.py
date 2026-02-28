from datetime import datetime, timedelta

import matplotlib.dates as mdates
import calendar
import matplotlib.pyplot as plt
import numpy as np


def calculate_daylight_hours(day_of_year: int, latitude: float) -> float:
    # Склонение по формуле Купера
    declination = 23.45 * np.sin(np.radians(360 * (284 + day_of_year) / 365))

    # Преобразуем в радианы
    lat_rad = np.radians(latitude)
    dec_rad = np.radians(declination)

    # Учет атмосферной рефракции (стандартная поправка -0.83°)
    # Для практических расчетов часто используют -0.8333°
    refraction_correction = np.radians(0.8333)

    # Вычисляем часовой угол с учетом рефракции
    cos_h = -np.tan(lat_rad) * np.tan(dec_rad) - np.sin(refraction_correction) / (np.cos(lat_rad) * np.cos(dec_rad))

    # Ограничиваем значение
    cos_h = np.clip(cos_h, -1.0, 1.0)

    if cos_h >= 1:
        return 0.0  # Полярная ночь
    if cos_h <= -1:
        return 24.0  # Полярный день

    # Продолжительность дня в часах
    h = np.degrees(np.arccos(cos_h))
    daylight = 2 * h / 15.0

    return daylight


def plot_daylight_duration(latitude, year=None, show_solstices=True):
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
        year = datetime.now().year

    # Проверяем високосный ли год
    days_in_year = 366 if calendar.isleap(year) else 365

    # Создаем массивы данных
    days = list(np.arange(1, days_in_year + 1))
    daylight_hours = np.array([calculate_daylight_hours(day, latitude) for day in days])

    # Создаем даты для оси X
    dates_ticks = [datetime(year, 1, 1) + timedelta(days=int(day - 1)) for day in days]

    # Рисуем основной график
    ax.plot(dates_ticks, daylight_hours, 'b-', linewidth=2, label=f'Длина дня')
    ax.fill_between(dates_ticks, 0, daylight_hours, alpha=0.3, color='skyblue')

    # Скорость изменения длины дня
    # daylight_derivative = np.gradient(daylight_hours) * 80 + 12
    # ax.plot(dates, daylight_derivative, 'g-', linewidth=2, label=f'Скорость изменения')

    # Настройки графика
    # ax.set_xlabel('Дата', fontsize=12)
    ax.set_ylabel('Продолжительность дня (часы)', fontsize=12)
    ax.set_title(f'Продолжительность светового дня в течение года', fontsize=14, fontweight='bold')

    # Настройка оси X (даты)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax.xaxis.set_minor_locator(mdates.WeekdayLocator())

    # Настройка оси Y
    ax.set_ylim(0, 24)
    ax.set_yticks(np.arange(0, 25, 2))
    ax.grid(True, alpha=0.5, linestyle='--')

    # Линия для 12 часов
    ax.axhline(y=12, color='gray', linestyle=':', alpha=0.5, label='12 часов')

    # Добавляем информацию о солнцестояниях и равноденствиях
    if show_solstices:
        # Даты солнцестояний и равноденствий (приблизительно)
        events = {
            'Весеннее равноденствие': datetime(year, 3, 20),
            'Летнее солнцестояние': datetime(year, 6, 21),
            'Осеннее равноденствие': datetime(year, 9, 22),
            'Зимнее солнцестояние': datetime(year, 12, 21),
            'Сегодня': datetime(year, datetime.now().month, datetime.now().day)
        }

        for event_name, event_date in events.items():
            # Находим ближайший день в массиве
            idx = min(range(len(dates_ticks)), key=lambda i: abs((dates_ticks[i] - event_date).days))
            hours = daylight_hours[idx]

            # Добавляем вертикальную линию и текст
            if event_name == 'Сегодня':
                event_name = 'Сегодня\n' + datetime.strftime(datetime.now(), '%d.%m.%Y')
                color = 'red'
                dot_color = 'ro'
                line_style = '-'
                y_cor = hours + 0.5
            else:
                color = 'blue'
                dot_color = 'bo'
                line_style = '--'
                y_cor = 1

            ax.axvline(x=event_date, color=color, linestyle=line_style, alpha=0.5)
            ax.plot(event_date, hours, dot_color, markersize=8)
            ax.text(event_date, y_cor, f'{event_name}\n{hours:.1f} ч',
                    ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

    # Добавляем статистику в легенду
    stats_text = (f'Широта: {latitude}°\n'
                  f'Min: {np.min(daylight_hours):.1f} ч\n'
                  f'Avg: {np.mean(daylight_hours):.1f} ч\n'
                  f'Max: {np.max(daylight_hours):.1f} ч')
    ax.text(0.99, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
            horizontalalignment='right', verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

    ax.legend(loc='upper left', fontsize=10)
    plt.xlim(datetime(year, 1, 1), datetime(year, 12, 31))

    return fig, ax


# Пример использования:
if __name__ == "__main__":
    fig, ax = plot_daylight_duration(latitude=55.66459, year=2026)

    filename = f"daylight_duration.png"
    fig.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Plot saved as '{filename}'")
