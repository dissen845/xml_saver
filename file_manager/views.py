from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
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
