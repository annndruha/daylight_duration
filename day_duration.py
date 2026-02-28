import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import matplotlib.dates as mdates

# def calculate_daylight_hours(day_of_year, latitude):
#     """
#     Рассчитывает продолжительность светового дня для заданного дня года и широты.

#     Параметры:
#     day_of_year (int): день года (1-365/366)
#     latitude (float): географическая широта в градусах

#     Возвращает:
#     float: продолжительность светового дня в часах
#     """
#     # Преобразуем день года в угол (в радианах)
#     # 21 декабря - зимнее солнцестояние (самый короткий день)
#     days_in_year = 365
#     declination_angle = 23.44 * np.sin(2 * np.pi * (284 + day_of_year) / 365.25)
#     # declination_angle = -23.44 * np.cos(2 * np.pi * (day_of_year + 10) / days_in_year)

#     # Переводим углы в радианы
#     lat_rad = np.radians(latitude)
#     dec_rad = np.radians(declination_angle)

#     # Вычисляем часовой угол заката
#     value_for_arccos = -np.tan(lat_rad) * np.tan(dec_rad)
#     if value_for_arccos < -1:
#         hour_angle = np.pi
#     elif value_for_arccos > 1:
#         hour_angle = 0
#     else:
#         hour_angle = np.arccos(value_for_arccos)

#     # Продолжительность дня в часах
#     daylight_hours = 24 * hour_angle / (np.pi)

#     return daylight_hours


def calculate_daylight_hours(day_of_year, latitude):
    # improved_daylight_calculation
    """
    Еще один улучшенный метод расчета.
    Использует упрощенную, но более точную формулу.
    """
    # Упрощенная, но достаточно точная формула
    days_in_year = 365.25

    # Склонение по упрощенной формуле Коопера
    declination = 23.45 * np.sin(np.radians(360 * (284 + day_of_year) / 365))

    # Преобразуем в радианы
    lat_rad = np.radians(latitude)
    dec_rad = np.radians(declination)

    # Учет атмосферной рефракции (стандартная поправка -0.83°)
    # Для практических расчетов часто используют -0.8333°
    refraction_correction = np.radians(0.8333)

    # Вычисляем часовой угол с учетом рефракции
    cos_h = -np.tan(lat_rad) * np.tan(dec_rad) - \
            np.sin(refraction_correction) / (np.cos(lat_rad) * np.cos(dec_rad))

    # Ограничиваем значение
    cos_h = np.clip(cos_h, -1.0, 1.0)

    if cos_h >= 1:
        return 0.0  # Полярная ночь
    elif cos_h <= -1:
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
    # Устанавливаем год
    if year is None:
        year = datetime.now().year

    # Проверяем високосный ли год
    is_leap_year = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
    days_in_year = 366 if is_leap_year else 365

    # Создаем массивы данных
    days = np.arange(1, days_in_year + 1)
    daylight_hours = np.array([calculate_daylight_hours(day, latitude) for day in days])

    daylight_derivative = np.gradient(daylight_hours) * 80 + 12

    # Создаем даты для оси X
    start_date = datetime(year, 1, 1)
    dates = [start_date + timedelta(days=int(day-1)) for day in days]

    # Создаем график
    fig, ax = plt.subplots(figsize=(12, 6))

    # Рисуем основной график
    ax.plot(dates, daylight_hours, 'b-', linewidth=2, label=f'Длина дня (Широта: {latitude}°)')
    ax.plot(dates, daylight_derivative, 'g-', linewidth=2, label=f'Скорость изменения (Широта: {latitude}°)')
    ax.fill_between(dates, 0, daylight_hours, alpha=0.3, color='skyblue')

    # Настройки графика
    ax.set_xlabel('Дата', fontsize=12)
    ax.set_ylabel('Продолжительность дня (часы)', fontsize=12)
    ax.set_title(f'Продолжительность светового дня в течение года', fontsize=14, fontweight='bold')

    # Настройка оси X (даты)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax.xaxis.set_minor_locator(mdates.WeekdayLocator())

    # Настройка оси Y
    ax.set_ylim(0, 24)
    ax.set_yticks(np.arange(0, 25, 2))
    ax.grid(True, alpha=0.3, linestyle='--')

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
            idx = min(range(len(dates)), key=lambda i: abs((dates[i] - event_date).days))
            hours = daylight_hours[idx]

            # Добавляем вертикальную линию и текст
            color = 'red' if event_name == 'Сегодня' else 'blue'
            dot_color = 'ro' if event_name == 'Сегодня' else 'bo'
            lstyle = '-' if event_name == 'Сегодня' else '--'

            if event_name == 'Сегодня':
                event_name = 'Сегодня\n' + '.'.join(map(str, (datetime.now().day, datetime.now().month, datetime.now().year)))

            ax.axvline(x=event_date, color=color, linestyle=lstyle, alpha=0.5)
            ax.plot(event_date, hours, dot_color, markersize=8)
            ax.text(event_date, hours + 0.5, f'{event_name}\n{hours:.1f} ч',
                   ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

    # Вычисляем статистику
    max_daylight = np.max(daylight_hours)
    min_daylight = np.min(daylight_hours)
    avg_daylight = np.mean(daylight_hours)

    # Добавляем статистику в легенду
    stats_text = f'Макс: {max_daylight:.1f} ч\nМин: {min_daylight:.1f} ч\nСредн: {avg_daylight:.1f} ч'

    # Легенда
    ax.legend(loc='upper left', fontsize=10)

    # Добавляем статистику в угол графика
    ax.text(0.02, 0.02, stats_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='bottom', bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

    # Автоматическая настройка layout
    plt.tight_layout()

    return fig, ax

# Пример использования:
if __name__ == "__main__":
    fig, ax = plot_daylight_duration(55.66459, year=2026)

    filename = f"daylight_duration.png"
    fig.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"График сохранен как '{filename}'")
