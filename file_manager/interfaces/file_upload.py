from abc import ABC, abstractmethod

from django.core.files.uploadedfile import UploadedFile

from ..models import XMLFile


class FileValidator(ABC):
    """Интерфейс валидации загружаемого файла."""

    @abstractmethod
    def validate(self, uploaded_file: UploadedFile) -> None:
        """Проверяет корректность загруженного файла по правилам домена."""


class FileRepository(ABC):
    """Интерфейс сохранения файла в хранилище и привязки к записи в БД."""

    @abstractmethod
    def save(self, uploaded_file: UploadedFile) -> XMLFile:
        """Сохраняет файл и возвращает связанный ORM-объект."""


class FileInfoBuilder(ABC):
    """Интерфейс формирования метаданных о сохранённом файле для ответа/API."""

    @abstractmethod
    def build(self, file_record: XMLFile) -> dict:
        """Формирует словарь с данными о файле."""
