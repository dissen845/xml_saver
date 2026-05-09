from django.http import JsonResponse


def health_check(_):
    """
    Простой healthcheck: всегда отвечает 200 OK
    и сообщает, что сервис работает.
    """

    data = {"status": "ok"}
    return JsonResponse(data)
