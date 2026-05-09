from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from .models import XMLFile

from .services.xml_service import XMLFileService, XMLFileValidationError


@require_GET
def health_check(_) -> JsonResponse:
    """
    Простой healthcheck: всегда отвечает 200 OK
    и сообщает, что сервис работает.
    """

    data = {"status": "ok"}
    return JsonResponse(data)


@require_POST
@csrf_exempt
def upload_xml(request: HttpRequest) -> JsonResponse:
    """
    Принимает POST-запрос с XML-файлом в поле "file".
    Сохраняет файл и возвращает JSON с информацией о сохранённом объекте.
    """

    # Проверяем, что файл передан в запросе
    if "file" not in request.FILES:
        return JsonResponse(status=400, data={"error": "Не передан файл"})

    uploaded_file = request.FILES["file"]

    try:
        xml_file = XMLFileService.process_xml_upload(uploaded_file)
        file_info = XMLFileService.get_file_info(xml_file)
        return JsonResponse(file_info, status=201)

    except XMLFileValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)

    # Неожиданная ошибка
    except Exception as e:
        return JsonResponse(
            {"error": "Внутренняя ошибка сервера", "detail": str(e)},
            status=500
        )


def download_xml(_, file_id: int):
    """
    Выдаем файл по его id
    """

    # Достаём объект по ID или возвращаем 404
    xml_file = get_object_or_404(XMLFile, pk=file_id)
    # Открываем файл из хранилища (работает с S3 и локальным диском)
    file = xml_file.file.open('rb')
    response = FileResponse(file, content_type='application/xml')

    return response