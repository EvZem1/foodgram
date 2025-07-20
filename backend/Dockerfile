FROM python:3.9-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код проекта в рабочую директорию
COPY . .

# Открываем порт, на котором будет работать Gunicorn
EXPOSE 8000

# Команда для запуска приложения
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0.0.0.0:8000"]