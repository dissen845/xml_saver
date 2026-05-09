from django.test import TestCase


class HealthCheckTest(TestCase):

    def test_health_returns_200_and_ok(self):
        response = self.client.get("/health_check/")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok"})
