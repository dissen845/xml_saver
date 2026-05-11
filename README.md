# xml_saver

Сервис на Django для загрузки, валидации, хранения и скачивания XML-файлов.

## Что умеет

- принимает XML-файл через HTTP (`POST /upload/xml/`);
- проверяет расширение файла (`.xml`) и валидность XML-содержимого;
- сохраняет файл в локальное хранилище или S3-совместимое хранилище (например, MinIO);
- выдает информацию о загруженном файле (id, имя, размер, время, URL скачивания);
- отдает файл по id (`GET /xml/<file_id>/`);
- имеет healthcheck (`GET /health_check/`).

## Технологии

- Python 3.12
- Django
- PostgreSQL
- Gunicorn
- boto3 + django-storages (для S3/MinIO)
- Pipenv

## Структура проекта

- `config/` - настройки Django и root URL-роутинг;
- `file_manager/` - приложение с моделями, вью и сервисом работы с XML;
- `file_manager/services/xml_service.py` - бизнес-логика валидации и сохранения;
- `docker-compose.yaml` - локальный стек: Postgres + MinIO + приложение;
- `entrypoint.sh` - создание бакета, миграции, collectstatic, запуск Gunicorn.

## Конфигурация

Основные переменные окружения:

- `STORAGE_TYPE` - `local` (по умолчанию) или `s3`;
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`;
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`;
- `AWS_S3_REGION_NAME`, `AWS_S3_ENDPOINT_URL`, `AWS_S3_USE_SSL`, `AWS_S3_VERIFY`.

Примечание: в текущем `config/settings.py` `DEBUG`, `SECRET_KEY` и `ALLOWED_HOSTS` заданы статически.

## Быстрый старт (Docker Compose)

1. Запустить сервисы:

```bash
docker-compose up -d --build
```

2. Приложение будет доступно на `http://localhost:8000`.
3. MinIO Console: `http://localhost:9001` (`minioadmin` / `minioadmin`).

## Локальный запуск (без Docker)

1. Установить зависимости:

```bash
pipenv install
```

2. Активировать окружение:

```bash
pipenv shell
```

3. Поднять PostgreSQL и задать переменные окружения (или использовать значения по умолчанию из `settings.py`).
4. Выполнить миграции:

```bash
python manage.py migrate
```

5. Запустить сервер:

```bash
python manage.py runserver
```

## API

### Healthcheck

- `GET /health_check/`

Ответ:

```json
{"status": "ok"}
```

### Загрузка XML

- `POST /upload/xml/`
- Form-data поле: `file`

Пример:

```bash
curl -X POST \
  -F "file=@./example.xml" \
  http://localhost:8000/upload/xml/
```

Успешный ответ (`201`):

```json
{
  "id": 1,
  "original_name": "example.xml",
  "uploaded_at": "2026-05-09 12:00:00",
  "size": 123,
  "url": "/xml/1/"
}
```

Ошибки:

- `400 {"error": "Не передан файл"}`
- `400 {"error": "Файл должен быть расширения .xml"}`
- `400 {"error": "Недействительный XML файл"}`
- `500 {"error": "Внутренняя ошибка сервера", "detail": "..."}`

### Скачивание XML

- `GET /xml/<file_id>/`

Пример:

```bash
curl -O -J http://localhost:8000/xml/1/
```
Успешный ответ (`200`):

```XML
<?xml version="1.0" encoding="UTF-8"?>
<user>
    <name>Иван Петров</name>
    <email>ivan@example.com</email>
    <age>35</age>
</user>
```