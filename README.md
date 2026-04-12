# Сервис автоматической проверки работ по нормализации БД

Веб-приложение для преподавателя и студента: загрузка эталона в Excel (`.xlsx`), генерация очищенного шаблона с техническими метаданными, автоматическая проверка ответов по заданиям 1–9, 11, 13, ручная проверка 10 и 12, комментарии и файлы от преподавателя.

## Стек

- Python 3.12, FastAPI, Jinja2, SQLAlchemy 2.0, Alembic, openpyxl, Pydantic, bcrypt, itsdangerous (сессии)
- **PostgreSQL** (драйвер `psycopg` v3); в Docker — сервис `db` в `docker-compose.yml`
- pytest для тестов

## Архитектура (слои)

- `app/api` — маршруты, сессии
- `app/services` — сценарии (эталон, шаблон, проверка, отзыв преподавателя)
- `app/repositories` — доступ к БД
- `app/checker` — `common` (SectionLocator, WorkbookValidator, метаданные), `normalizers`, `parsers/*`, `checkers/*`, `engine.py`, `fd_algebra.py`
- `app/domain` — предметные структуры (ParsedWorkbook, отчёт проверки и т.д.)
- `app/models` — SQLAlchemy ORM
- `app/templates`, `app/static` — UI

## Запуск через Docker

```bash
docker compose up --build
```

Приложение: `http://localhost:8000`

Поднимаются **PostgreSQL 16** и веб-сервис; данные БД — том `pg_data`, загруженные файлы — `upload_data`.

Строка подключения по умолчанию в compose:

`postgresql+psycopg://dn_user:dn_pass@db:5432/dn_db`

Переменные см. `.env.example`.

## Локальный запуск (без Docker)

Нужны **Python 3.10+** и **запущенный PostgreSQL** с созданной БД и пользователем (см. `.env.example`).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
export DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/dn_db
export UPLOAD_DIR=./uploads
mkdir -p uploads
alembic upgrade head
uvicorn app.main:app --reload
```

## Демо-пользователи

После первого старта создаются роли и пользователи (пароли хранятся как bcrypt-хеш):

| Логин   | Пароль  | Роль    |
|---------|---------|---------|
| admin   | admin   | admin   |
| teacher | teacher | teacher |
| student | student | student |

## Workflow

1. **Преподаватель** входит, загружает эталон `.xlsx`, при необходимости отмечает «Опубликовать».
2. **Студент** видит опубликованные работы, скачивает шаблон (ответы в секциях очищены, в книге есть скрытые метаданные и лист `__template_meta__`).
3. Студент заполняет файл и отправляет его; при повреждённых метаданных можно указать **ID версии эталона** в форме.
4. Система парсит секции устойчиво (поиск «Задание №N» по ячейкам), запускает проверки по заданиям, сохраняет отчёт.
5. Преподаватель просматривает попытку, может оставить комментарий и загрузить проверенный файл; студент скачивает файл и читает комментарий.

## Ограничения

- Один лист, секции «Задание №1» … «Задание №13».
- Автопроверка: задания 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 13; 10 и 12 только сохранение и отображение.
- Режим **training/testing** и флаг «опциональные чистые связующие отношения» задаются на уровне варианта (`variants`); отображение деталей эталона в режиме testing можно доработать в шаблонах (полный отчёт хранится в БД).

## Тесты

```bash
pytest tests/
```

## Структура каталогов

```
app/
  api/           # deps, session
  checker/       # engine, parsers, checkers, normalizers, common, reference_compiler
  core/          # config, security, logging
  db/            # session, seed
  domain/
  models/
  repositories/
  services/
  templates/
  static/
  main.py
alembic/
tests/
```

## Ключевые решения

- **Метаданные шаблона:** дублирование в скрытых ячейках (колонка `ZZ`) и на скрытом листе `__template_meta__`; при чтении приоритет у согласованного источника с большей `template_version`.
- **Fallback:** если метаданные не читаются, обязателен выбор **версии эталона** в форме (сервер не доверяет только данным из файла без согласования с доступом).
- **Проверка:** отдельные парсеры и чекеры по заданиям; канонизация ФЗ и сравнение множеств, а не побайтовое сравнение Excel.
