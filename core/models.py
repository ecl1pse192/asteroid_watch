from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Asteroid(models.Model):
    """Модель астероида - справочник уникальных небесных тел."""
    nasa_id = models.CharField(max_length=50, unique=True, verbose_name='NASA ID')
    name = models.CharField(max_length=200, verbose_name='Название')
    absolute_magnitude = models.FloatField(null=True, blank=True, verbose_name='Абсолютная звёздная величина')
    is_potentially_hazardous = models.BooleanField(default=False, verbose_name='Потенциально опасный')
    nasa_jpl_url = models.URLField(max_length=500, blank=True, verbose_name='URL на сайте NASA JPL')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Астероид'
        verbose_name_plural = 'Астероиды'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.nasa_id})"


class Flyby(models.Model):
    """Модель сближения астероида с Землёй."""
    asteroid = models.ForeignKey(Asteroid, on_delete=models.CASCADE, related_name='flybys', verbose_name='Астероид')
    date = models.DateTimeField(verbose_name='Дата сближения')
    velocity_kmh = models.FloatField(verbose_name='Скорость (км/ч)')
    miss_distance_km = models.FloatField(verbose_name='Дистанция промаха (км)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Сближение'
        verbose_name_plural = 'Сближения'
        ordering = ['-date']
        unique_together = ['asteroid', 'date']

    def __str__(self):
        return f"{self.asteroid.name} - {self.date.strftime('%Y-%m-%d %H:%M')}"


class Watchlist(models.Model):
    """Модель списка отслеживания пользователя."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist_items', verbose_name='Пользователь')
    asteroid = models.ForeignKey(Asteroid, on_delete=models.CASCADE, related_name='watchlist_items', verbose_name='Астероид')
    user_notes = models.TextField(blank=True, verbose_name='Заметки пользователя')
    added_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        verbose_name = 'Элемент списка отслеживания'
        verbose_name_plural = 'Списки отслеживания'
        ordering = ['-added_at']
        unique_together = ['user', 'asteroid']

    def __str__(self):
        return f"{self.user.username} - {self.asteroid.name}"
