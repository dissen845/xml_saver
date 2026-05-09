#!/bin/bash
set -e

echo "Проверяем и создаём S3-бакет"
python -c "
import boto3, os
if os.environ.get('STORAGE_TYPE') == 's3':
  s3 = boto3.client(
      's3',
      aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
      aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
      endpoint_url=os.environ.get('AWS_S3_ENDPOINT_URL'),
      use_ssl=os.environ.get('AWS_S3_USE_SSL', 'true').lower() == 'true',
      verify=os.environ.get('AWS_S3_VERIFY', 'true').lower() == 'true',
      region_name=os.environ.get('AWS_S3_REGION_NAME')
  )
  bucket_name = os.environ.get('AWS_STORAGE_BUCKET_NAME')
  try:
      s3.head_bucket(Bucket=bucket_name)
      print(f'Бакет {bucket_name} уже существует.')
  except Exception:
      s3.create_bucket(Bucket=bucket_name)
      print(f'Бакет {bucket_name} успешно создан.')
"

echo "Применяем миграции..."
python manage.py migrate --noinput

echo "Собираем статические файлы..."
python manage.py collectstatic --noinput

echo "Запускаем Gunicorn..."
gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -