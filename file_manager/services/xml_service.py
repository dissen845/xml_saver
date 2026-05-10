import xml.etree.ElementTree as ET
from django.core.files.uploadedfile import UploadedFile
from django.urls import reverse
from ..models import XMLFile


class XMLFileValidationError(Exception):
    """Кастомное исключение для ошибок валидации XML."""
    pass


class XMLFileService:
    """Сервис для работы с XML-файлами."""

    @staticmethod
    def _validate_xml_file(uploaded_file: UploadedFile) -> None:
        """
        Проверяет, что файл является валидным XML.
        Args:
            uploaded_file: Загруженный файл
        Raises:
            XMLFileValidationError: Если файл не XML или невалидный
        """

        # Проверка расширения
        if not uploaded_file.name.lower().endswith(".xml"):
            raise XMLFileValidationError("Файл должен быть расширения .xml")
        # Проверка содержимого
        try:
            xml_content = uploaded_file.read()
            ET.fromstring(xml_content)
        except ET.ParseError:
            raise XMLFileValidationError("Недействительный XML файл")
        except Exception as e:
            raise XMLFileValidationError(f"Ошибка при чтении файла: {str(e)}")
        finally:
            uploaded_file.seek(0)

    @staticmethod
    def _save_xml_file(uploaded_file: UploadedFile) -> XMLFile:
        """
        Сохраняет XML-файл в хранилище и создаёт запись в БД.
        Args:
            uploaded_file: загруженный файл
        Returns:
            XMLFile: сохранённый объект модели
        """

        xml_file = XMLFile(
            file=uploaded_file,
            original_name=uploaded_file.name,
            size=uploaded_file.size,
        )
        xml_file.save()
        return xml_file

    @classmethod
    def process_xml_upload(cls, uploaded_file: UploadedFile) -> XMLFile:
        """
        Полный процесс обработки загруженного XML-файла:
        валидация + сохранение.
        Args:
            uploaded_file: Загруженный файл
        Returns:
            XMLFile: Сохранённый объект модели
        Raises:
            XMLFileValidationError: Если файл не прошёл валидацию
        """

        # Проверка
        cls._validate_xml_file(uploaded_file)

        # Сохраняем
        return cls._save_xml_file(uploaded_file)

    @staticmethod
    def get_file_info(xml_file: XMLFile) -> dict:
        """
        Формирует словарь с информацией о сохранённом файле.
        Args:
            xml_file: Объект ORM модели XMLFile
        Returns:
            dict: Словарь с данными
        """

        info = {
            "id": xml_file.id,
            "original_name": xml_file.original_name,
            "uploaded_at": xml_file.uploaded_at.strftime("%Y-%m-%d %H:%M:%S"),
            "size": xml_file.file.size if xml_file.file else None,
        }

        info["url"] = reverse(
            "download_xml",
            kwargs={"file_id": xml_file.id},
        )
        return info
