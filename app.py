from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import os
from datetime import datetime

app = Flask(__name__)

# Пути к файлам с данными
HISTORY_DATA_PATH = 'data/solar_activity_1749-2024.txt'
FUTURE_DATA_PATH = 'data/solar_activity_2025-2069.csv'


# Загрузка данных
def load_history_data():
    # Читаем данные, пропуская возможные заголовки и обрабатывая разделитель табуляции
    df = pd.read_csv(HISTORY_DATA_PATH, sep='\t', header=None,
                    names=['year', 'activity'], skiprows=1,
                    dtype={'year': int, 'activity': float})
    return df


def load_future_data():
    return pd.read_csv(FUTURE_DATA_PATH, names=['month', 'activity'])


# Генерация графика
def generate_plot(start_year, start_month, end_year, end_month):
    df = load_future_data()

    # Преобразование месяцев в даты для правильного порядка
    start_idx = (start_year - 2025) * 12 + start_month - 1
    end_idx = (end_year - 2025) * 12 + end_month - 1

    if start_idx > end_idx:
        start_idx, end_idx = end_idx, start_idx

    data = df.iloc[start_idx:end_idx + 1]

    # Создание графика
    plt.figure(figsize=(12, 6))
    plt.plot(data['month'], data['activity'], 'r-', linewidth=2)
    plt.title(f'Солнечная активность с {start_month}/{start_year} по {end_month}/{end_year}', fontsize=14)
    plt.xlabel('Время в месяцах', fontsize=12)
    plt.ylabel('Количество солнечных пятен', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Преобразование в base64 для отображения в HTML
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    return plot_url


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/history', methods=['GET', 'POST'])
def history():
    activity = None
    year = None
    error = None

    if request.method == 'POST':
        try:
            year = int(request.form['year'])
            if year < 1749 or year > 2024:
                error = "Год должен быть в диапазоне 1749-2024"
            else:
                df = load_history_data()
                result = df[df['year'] == year]

                if not result.empty:
                    activity = float(result.iloc[0]['activity'])
                else:
                    error = "Данные за указанный год не найдены"
        except ValueError:
            error = "Пожалуйста, введите корректный год"
        except Exception as e:
            error = f"Произошла ошибка: {str(e)}"

    return render_template('history.html', activity=activity, year=year, error=error)


@app.route('/calculation', methods=['GET', 'POST'])
def calculation():
    activity = None
    year = None
    month = None
    rotation = None

    if request.method == 'POST':
        year = int(request.form['year'])
        month = int(request.form['month'])

        if 2025 <= year <= 2069 and 1 <= month <= 12:
            month_idx = (year - 2025) * 12 + month - 1
            df = load_future_data()
            activity = df.iloc[month_idx]['activity']
            rotation = (activity / 200 * 180)  # Ограничиваем максимальное значение 200 для шкалы

    return render_template('calculation.html', activity=activity, year=year, month=month, rotation=rotation)


@app.route('/graph', methods=['GET', 'POST'])
def graph():
    plot_url = None

    if request.method == 'POST':
        start_year = int(request.form['start_year'])
        start_month = int(request.form['start_month'])
        end_year = int(request.form['end_year'])
        end_month = int(request.form['end_month'])

        plot_url = generate_plot(start_year, start_month, end_year, end_month)

    return render_template('graph.html', plot_url=plot_url)


if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    app.run(debug=True)