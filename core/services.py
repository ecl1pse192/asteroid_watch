"""Сервис для работы с NASA NeoWs API."""
import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import Asteroid, Flyby


class NASANeoWsService:
    """Сервис для получения данных о сближениях астероидов с Землёй."""
    
    @classmethod
    def get_base_url(cls):
        return getattr(settings, 'NASA_NEO_API_URL', 'https://api.nasa.gov/neo/rest/v1/feed')
    
    @classmethod
    def get_api_key(cls):
        return getattr(settings, 'NASA_API_KEY', '') or 'DEMO_KEY'
    
    @classmethod
    def fetch_week_data(cls, start_date=None, end_date=None):
        """
        Получает данные о сближениях астероидов за неделю.
        
        Args:
            start_date: Дата начала периода (datetime или str). Если None, используется сегодня.
            end_date: Дата конца периода (datetime или str). Если None, используется start_date + 7 дней.
        
        Returns:
            dict: Данные от NASA API или None в случае ошибки
        """
        if start_date is None:
            start_date = timezone.now().date()
        elif isinstance(start_date, datetime):
            start_date = start_date.date()
        elif isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if end_date is None:
            end_date = start_date + timedelta(days=7)
        elif isinstance(end_date, datetime):
            end_date = end_date.date()
        elif isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        params = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'api_key': cls.get_api_key()
        }
        
        try:
            response = requests.get(cls.get_base_url(), params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе к NASA API: {e}")
            return None
    
    @classmethod
    def process_and_save_data(cls, data):
        """
        Обрабатывает данные от NASA API и сохраняет в базу данных.
        
        Args:
            data: Словарь с данными от NASA API
        
        Returns:
            tuple: (количество созданных астероидов, количество созданных сближений)
        """
        if not data or 'near_earth_objects' not in data:
            return 0, 0
        
        asteroids_created = 0
        flybys_created = 0
        
        # Проходим по всем дням в ответе
        for date_str, asteroids_data in data['near_earth_objects'].items():
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Обрабатываем каждый астероид
            for asteroid_data in asteroids_data:
                try:
                    # Получаем или создаём астероид
                    asteroid, created = cls._get_or_create_asteroid(asteroid_data)
                    if created:
                        asteroids_created += 1
                    
                    # Обрабатываем все сближения для этого астероида в этот день
                    close_approach_data = asteroid_data.get('close_approach_data', [])
                    for approach in close_approach_data:
                        flyby, created = cls._get_or_create_flyby(
                            asteroid, approach, date
                        )
                        if created:
                            flybys_created += 1
                            
                except Exception as e:
                    print(f"Ошибка при обработке астероида {asteroid_data.get('id', 'unknown')}: {e}")
                    continue
        
        return asteroids_created, flybys_created
    
    @classmethod
    def _get_or_create_asteroid(cls, asteroid_data):
        """Получает или создаёт астероид из данных NASA API."""
        nasa_id = asteroid_data.get('id')
        if not nasa_id:
            raise ValueError("NASA ID не найден в данных")
        
        name = asteroid_data.get('name', 'Unknown')
        absolute_magnitude = asteroid_data.get('absolute_magnitude_h')
        is_hazardous = asteroid_data.get('is_potentially_hazardous_asteroid', False)
        nasa_jpl_url = asteroid_data.get('nasa_jpl_url', '')
        
        asteroid, created = Asteroid.objects.get_or_create(
            nasa_id=nasa_id,
            defaults={
                'name': name,
                'absolute_magnitude': absolute_magnitude,
                'is_potentially_hazardous': is_hazardous,
                'nasa_jpl_url': nasa_jpl_url,
            }
        )
        
        # Обновляем данные, если астероид уже существует
        if not created:
            update_fields = []
            if asteroid.name != name:
                asteroid.name = name
                update_fields.append('name')
            if asteroid.absolute_magnitude != absolute_magnitude:
                asteroid.absolute_magnitude = absolute_magnitude
                update_fields.append('absolute_magnitude')
            if asteroid.is_potentially_hazardous != is_hazardous:
                asteroid.is_potentially_hazardous = is_hazardous
                update_fields.append('is_potentially_hazardous')
            if asteroid.nasa_jpl_url != nasa_jpl_url:
                asteroid.nasa_jpl_url = nasa_jpl_url
                update_fields.append('nasa_jpl_url')
            if update_fields:
                asteroid.save(update_fields=update_fields)
        
        return asteroid, created
    
    @classmethod
    def _get_or_create_flyby(cls, asteroid, approach_data, date):
        """Получает или создаёт сближение из данных NASA API."""
        # Парсим дату и время
        approach_date_str = approach_data.get('close_approach_date_full')
        if approach_date_str:
            try:
                approach_datetime = datetime.strptime(
                    approach_date_str, '%Y-%b-%d %H:%M'
                )
                approach_datetime = timezone.make_aware(approach_datetime)
            except ValueError:
                # Если формат не подходит, используем только дату
                approach_datetime = timezone.make_aware(
                    datetime.combine(date, datetime.min.time())
                )
        else:
            approach_datetime = timezone.make_aware(
                datetime.combine(date, datetime.min.time())
            )
        
        # Получаем скорость (конвертируем км/с в км/ч)
        velocity_data = approach_data.get('relative_velocity', {})
        velocity_kms = float(velocity_data.get('kilometers_per_second', 0))
        velocity_kmh = velocity_kms * 3600  # Конвертация в км/ч
        
        # Получаем расстояние промаха
        miss_distance_data = approach_data.get('miss_distance', {})
        miss_distance_km = float(miss_distance_data.get('kilometers', 0))
        
        flyby, created = Flyby.objects.get_or_create(
            asteroid=asteroid,
            date=approach_datetime,
            defaults={
                'velocity_kmh': velocity_kmh,
                'miss_distance_km': miss_distance_km,
            }
        )
        
        return flyby, created
