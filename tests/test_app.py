import os
import unittest

from app import app


class PromptlyTestCase(unittest.TestCase):
    def setUp(self):
        os.environ.pop("MODEL_API_URL", None)
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_home_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Your local AI workspace", response.data)

    def test_form_returns_demo_response(self):
        response = self.client.post("/", data={"prompt": "Hello model"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"This is a demo response", response.data)

    def test_json_api_validates_empty_prompt(self):
        response = self.client.post("/api/generate", json={"prompt": ""})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
