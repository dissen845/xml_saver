import tempfile
from unittest.mock import Mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from file_manager.models import XMLFile
from file_manager.services.xml_service import (
    XMLFileInfoBuilder,
    XMLFileRepository,
    XMLFileService,
    XMLFileValidationError,
    XMLUploadProcessor,
    XMLValidator,
)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class HealthCheckTest(TestCase):
    def test_health_returns_200_and_ok(self):
        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok"})


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class UploadXMLViewTest(TestCase):
    def test_upload_xml_returns_400_when_file_not_provided(self):
        response = self.client.post(reverse("upload_xml"))
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {"error": "Не передан файл"})

    def test_upload_xml_returns_400_for_invalid_extension(self):
        invalid_file = SimpleUploadedFile(
            "not_xml.txt",
            b"<root><child/></root>",
            content_type="text/plain",
        )

        response = self.client.post(
            reverse("upload_xml"),
            data={"file": invalid_file},
        )

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {"error": "Файл должен быть расширения .xml"})

    def test_upload_xml_returns_400_for_invalid_xml(self):
        broken_xml = SimpleUploadedFile(
            "broken.xml",
            b"<root><child></root>",
            content_type="application/xml",
        )

        response = self.client.post(reverse("upload_xml"), data={"file": broken_xml})

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {"error": "Недействительный XML файл"})

    def test_upload_xml_saves_file_and_returns_metadata(self):
        payload = b"<root><item>42</item></root>"
        xml_file = SimpleUploadedFile("valid.xml", payload, content_type="application/xml")

        response = self.client.post(reverse("upload_xml"), data={"file": xml_file})

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["original_name"], "valid.xml")
        self.assertEqual(body["size"], len(payload))
        self.assertIn("uploaded_at", body)
        self.assertIn("id", body)
        self.assertEqual(body["url"], reverse("download_xml", kwargs={"file_id": body["id"]}))
        self.assertTrue(XMLFile.objects.filter(pk=body["id"]).exists())


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class DownloadXMLViewTest(TestCase):
    def test_download_xml_returns_404_for_unknown_file(self):
        response = self.client.get(reverse("download_xml", kwargs={"file_id": 99999}))
        self.assertEqual(response.status_code, 404)

    def test_download_xml_returns_file_response(self):
        payload = b"<root><item>download</item></root>"
        uploaded = SimpleUploadedFile("file.xml", payload, content_type="application/xml")
        xml_file = XMLFileService.process_xml_upload(uploaded)

        response = self.client.get(reverse("download_xml", kwargs={"file_id": xml_file.id}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
        self.assertEqual(b"".join(response.streaming_content), payload)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class XMLFileServiceTest(TestCase):
    def test_process_xml_upload_creates_xml_file_object(self):
        uploaded = SimpleUploadedFile(
            "saved.xml",
            b"<root><saved/></root>",
            content_type="application/xml",
        )

        xml_file = XMLFileService.process_xml_upload(uploaded)

        self.assertTrue(XMLFile.objects.filter(pk=xml_file.pk).exists())
        self.assertEqual(xml_file.original_name, "saved.xml")
        self.assertEqual(xml_file.size, len(b"<root><saved/></root>"))

    def test_get_file_info_contains_expected_fields(self):
        uploaded = SimpleUploadedFile(
            "info.xml",
            b"<root><info/></root>",
            content_type="application/xml",
        )
        xml_file = XMLFileService.process_xml_upload(uploaded)

        info = XMLFileService.get_file_info(xml_file)

        self.assertEqual(info["id"], xml_file.id)
        self.assertEqual(info["original_name"], "info.xml")
        self.assertEqual(info["size"], xml_file.file.size)
        self.assertEqual(info["url"], reverse("download_xml", kwargs={"file_id": xml_file.id}))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class XMLComponentsTest(TestCase):
    def setUp(self):
        self.validator = XMLValidator()
        self.repository = XMLFileRepository()
        self.info_builder = XMLFileInfoBuilder()

    def test_default_validator_resets_pointer_after_success(self):
        uploaded = SimpleUploadedFile(
            "valid_component.xml",
            b"<root><child/></root>",
            content_type="application/xml",
        )

        self.validator.validate(uploaded)

        self.assertEqual(uploaded.tell(), 0)
        self.assertEqual(uploaded.read(), b"<root><child/></root>")

    def test_default_validator_raises_for_wrong_extension(self):
        uploaded = SimpleUploadedFile(
            "not_xml.txt",
            b"<root><child/></root>",
            content_type="text/plain",
        )

        with self.assertRaisesMessage(XMLFileValidationError, "Файл должен быть расширения .xml"):
            self.validator.validate(uploaded)

    def test_default_validator_raises_for_invalid_xml(self):
        uploaded = SimpleUploadedFile(
            "bad.xml",
            b"<root><bad></root>",
            content_type="application/xml",
        )

        with self.assertRaises(XMLFileValidationError):
            self.validator.validate(uploaded)

    def test_django_repository_saves_xmlfile_model(self):
        payload = b"<root><saved/></root>"
        uploaded = SimpleUploadedFile("repo.xml", payload, content_type="application/xml")

        xml_file = self.repository.save(uploaded)

        self.assertTrue(XMLFile.objects.filter(pk=xml_file.pk).exists())
        self.assertEqual(xml_file.original_name, "repo.xml")
        self.assertEqual(xml_file.size, len(payload))

    def test_info_builder_returns_expected_payload(self):
        uploaded = SimpleUploadedFile(
            "builder.xml",
            b"<root><item>1</item></root>",
            content_type="application/xml",
        )
        xml_file = XMLFileService.process_xml_upload(uploaded)

        info = self.info_builder.build(xml_file)

        self.assertEqual(info["id"], xml_file.id)
        self.assertEqual(info["original_name"], "builder.xml")
        self.assertEqual(info["size"], xml_file.file.size)
        self.assertEqual(info["url"], reverse("download_xml", kwargs={"file_id": xml_file.id}))


class XMLUploadProcessorTest(TestCase):
    def test_process_upload_calls_validator_then_repository(self):
        validator = Mock()
        repository = Mock()
        info_builder = Mock()
        uploaded = Mock()
        saved_xml = object()
        repository.save.return_value = saved_xml

        processor = XMLUploadProcessor(
            validator=validator,
            repository=repository,
            info_builder=info_builder,
        )

        result = processor.process_upload(uploaded)

        validator.validate.assert_called_once_with(uploaded)
        repository.save.assert_called_once_with(uploaded)
        self.assertIs(result, saved_xml)

    def test_build_file_info_delegates_to_info_builder(self):
        validator = Mock()
        repository = Mock()
        info_builder = Mock()
        xml_file = Mock()
        expected_info = {"id": 123}
        info_builder.build.return_value = expected_info

        processor = XMLUploadProcessor(
            validator=validator,
            repository=repository,
            info_builder=info_builder,
        )

        result = processor.build_file_info(xml_file)

        info_builder.build.assert_called_once_with(xml_file)
        self.assertEqual(result, expected_info)
