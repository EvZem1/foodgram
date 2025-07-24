"Фудграм" - это сайт, на котором пользователи могут публиковать свои рецепты с фотками, добавлять чужие (и свои) рецепты в избранное, подписываться на публикации других авторов, а также скачивать список покупок.

Проект развернут на сервере и доступен по адресу: http://89.169.166.27/

---

## Технологии

- Python 3.9
- Django 4.2
- Django REST Framework
- PostgreSQL
- Nginx
- Gunicorn
- Docker
- Docker Compose
- CI/CD (GitHub Actions)

---

## Инструкция по запуску проекта

1. **Клонировать репозиторий:**
   ```bash
   git clone [https://github.com/EvZem1/foodgram.git](https://github.com/EvZem1/foodgram.git)
   ```

2. **Перейти в папку infra:**
   ```bash
   cd foodgram/infra/
   ```

3. **Создать и заполнить файл `.env`** с переменными окружения по образцу:
   ```env
   POSTGRES_DB=foodgram
   POSTGRES_USER=foodgram_user
   POSTGRES_PASSWORD=foodgram_password
   DB_HOST=db
   DB_PORT=5432
   ```

4. **Запустить Docker Compose:**
   ```bash
   docker compose up --build -d
   ```

5. **Выполнить миграции, загрузить ингредиенты и собрать статику:**
   ```bash
   docker compose exec backend python manage.py migrate
   docker compose exec backend python manage.py load_ingredients
   docker compose exec backend python manage.py collectstatic --no-input
   ```

6. **Создать суперпользователя:**
   ```bash
   docker compose exec backend python manage.py createsuperuser
   ```

---

## Примеры запросов к API

- **Получение списка рецептов:** `GET /api/recipes/`
- **Создание пользователя:** `POST /api/users/`
- **Получение токена:** `POST /api/auth/token/login/`
- **Добавление рецепта в избранное:** `POST /api/recipes/{id}/favorite/`

Полная документация API доступна после запуска по адресу: `http://localhost/api/docs/`

---

## Автор

**Евгений Землянухин**
- GitHub: [https://github.com/EvZem1](https://github.com/EvZem1)
