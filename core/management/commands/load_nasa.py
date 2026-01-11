import requests
from django.core.management.base import BaseCommand
from django.conf import settings  
from django.utils import timezone 
from core.models import Asteroid, Flyby
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Загружает данные об астероидах с NASA API'

    def handle(self, *args, **kwargs):
        api_key = getattr(settings, 'NASA_API_KEY', 'DEMO_KEY')

        if not api_key:
             self.stdout.write(self.style.WARNING('API ключ не найден, используется DEMO_KEY'))

        today = timezone.now().date()
        end_date = today + timedelta(days=7)
        
        start_str = today.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        url = f'https://api.nasa.gov/neo/rest/v1/feed?start_date={start_str}&end_date={end_str}&api_key={api_key}'
        
        self.stdout.write(f'Запрашиваем данные: {start_str} - {end_str}...')

        try:
            response = requests.get(url, timeout=10) 
            
            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(f'ОШИБКА API: {response.status_code}'))
                self.stdout.write(self.style.ERROR(f'Детали: {response.text}'))
                return

            data = response.json()
            count = 0
            
            if 'near_earth_objects' not in data:
                 self.stdout.write(self.style.WARNING('API не вернул объектов.'))
                 return

            for date_str, asteroids in data['near_earth_objects'].items():
                for item in asteroids:
                    try:
                        asteroid, created = Asteroid.objects.update_or_create(
                            nasa_id=str(item['id']), 
                            defaults={
                                'name': item['name'],
                                'absolute_magnitude': item['absolute_magnitude_h'],
                                'is_potentially_hazardous': item['is_potentially_hazardous_asteroid'],
                                'nasa_jpl_url': item['nasa_jpl_url']
                            }
                        )
                        
                        for close_data in item['close_approach_data']:
                           
                            flyby_date_str = close_data['close_approach_date']
                           
                            flyby_date_obj = datetime.strptime(flyby_date_str, '%Y-%m-%d')
                       
                            flyby_date_aware = timezone.make_aware(flyby_date_obj)

                            Flyby.objects.update_or_create(
                                asteroid=asteroid,
                                date=flyby_date_aware, 
                                defaults={
                                    'velocity_kmh': float(close_data['relative_velocity']['kilometers_per_hour']),
                                    'miss_distance_km': float(close_data['miss_distance']['kilometers'])
                                }
                            )
                        count += 1
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"Ошибка с астероидом {item.get('name')}: {e}"))
            
            self.stdout.write(self.style.SUCCESS(f'УРА! Успешно обработано астероидов: {count}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Критическая ошибка скрипта: {e}'))