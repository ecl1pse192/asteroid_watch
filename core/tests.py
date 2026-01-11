from django.test import TestCase
from django.urls import reverse
from .models import Asteroid

class CoreViewsTest(TestCase):
    def test_index_page_loads(self):
        """Проверка, что главная страница открывается (код 200)."""
        response = self.client.get(reverse('core:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/index.html')

    def test_asteroid_model(self):
        """Проверка создания астероида."""
        ast = Asteroid.objects.create(
            nasa_id="12345",
            name="Test Asteroid",
            is_potentially_hazardous=True
        )
        self.assertEqual(str(ast), "Test Asteroid (12345)")