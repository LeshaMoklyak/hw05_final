from django.test import TestCase, Client


class CoreURLTests(TestCase):
    def test_404_page(self):
        self.guest_client = Client()
        response = self.guest_client.get('/nonexist-page/')
        self.assertTemplateUsed(response, 'core/404.html')
