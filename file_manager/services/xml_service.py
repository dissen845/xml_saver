import xml.etree.ElementTree as ET
from django.core.files.uploadedfile import UploadedFile
from django.urls import reverse

from ..interfaces import FileInfoBuilder, FileRepository, FileValidator
from ..models import XMLFile


class XMLFileValidationError(Exception):
    """Кастомное исключение для ошибок валидации XML."""
    pass


class XMLValidator(FileValidator):
    """Компонент валидации XML-файла."""

    def validate(self, uploaded_file: UploadedFile) -> None:
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

class XMLFileRepository(FileRepository):
    """Репозиторий для сохранения XML-файла через Django ORM."""

    def save(self, uploaded_file: UploadedFile) -> XMLFile:
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

class XMLFileInfoBuilder(FileInfoBuilder):
    """Формирует метаданные сохранённого XML-файла."""

    def build(self, file_record: XMLFile) -> dict:
        """
        Формирует словарь с информацией о сохранённом файле.
        Args:
            file_record: Объект ORM модели XMLFile
        Returns:
            dict: Словарь с данными
        """

        info = {
            "id": file_record.id,
            "original_name": file_record.original_name,
            "uploaded_at": file_record.uploaded_at.strftime("%Y-%m-%d %H:%M:%S"),
            "size": file_record.file.size if file_record.file else None,
        }

        info["url"] = reverse(
            "download_xml",
            kwargs={"file_id": file_record.id},
        )
        return info


class XMLUploadProcessor:
    """Оркестратор загрузки XML с внедряемыми зависимостями."""

    def __init__(
        self,
        validator: FileValidator,
        repository: FileRepository,
        info_builder: FileInfoBuilder,
    ) -> None:
        self.validator = validator
        self.repository = repository
        self.info_builder = info_builder

    def process_upload(self, uploaded_file: UploadedFile) -> XMLFile:
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

        self.validator.validate(uploaded_file)
        return self.repository.save(uploaded_file)

    def build_file_info(self, xml_file: XMLFile) -> dict:
        """
        Собирает словарь с метаданными сохранённого файла.
        Args:
            xml_file: Сохранённая запись модели XMLFile.
        Returns:
            dict: Поля вроде id, original_name, uploaded_at, size, url.
        """
        return self.info_builder.build(xml_file)


class XMLFileService:
    """Фасад для работы с XML-файлами."""

    _processor = XMLUploadProcessor(
        validator=XMLValidator(),
        repository=XMLFileRepository(),
        info_builder=XMLFileInfoBuilder(),
    )

    @classmethod
    def process_xml_upload(cls, uploaded_file: UploadedFile) -> XMLFile:
        return cls._processor.process_upload(uploaded_file)

    @classmethod
    def get_file_info(cls, xml_file: XMLFile) -> dict:
        return cls._processor.build_file_info(xml_file)
