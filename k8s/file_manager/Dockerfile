FROM python:3.12

ENV PYTHONUNBUFFERED=1

ARG BASE_DIR=bh/

WORKDIR /app

# Копирование файлов проекта
COPY ${BASE_DIR}/Pipfile ${BASE_DIR}/Pipfile.lock /app/

RUN pip install \
    virtualenv==20.25.0 \
    filelock==3.13.1 \
    pipenv==2023.11.15

RUN pipenv install --deploy --system

ADD ${BASE_DIR}/ /app/

# Создаём директории и пользователя
RUN useradd -m -s /bin/bash django && \
    chown -R django:django /app


EXPOSE 8000

# Команда для запуска приложения
ENTRYPOINT ["bash", "/app/entrypoint.sh"]
