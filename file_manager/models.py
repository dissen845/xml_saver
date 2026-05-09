from django.db import models


class XMLFile(models.Model):
    """
    Модель для хранения информации о загруженном XML-файле.
    """

    # Поле для хранения файла. upload_to – подпапка внутри MEDIA_ROOT
    file = models.FileField(upload_to="xml_files/")
    original_name = models.CharField(max_length=255)
    size = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # TODO Если в будущем планируется обработка XML, можно добавить поле статуса
    # processed = models.BooleanField(default=False)

    def __str__(self):
        return self.original_name
