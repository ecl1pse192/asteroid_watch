from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from .models import Asteroid, Flyby, Watchlist
from .services import NASANeoWsService


def index(request):
    """Главная страница - список астероидов на текущую неделю."""
    # Получаем сближения на текущую неделю
    today = timezone.now().date()
    week_end = today + timedelta(days=7)
    
    # Получаем фильтр для потенциально опасных объектов
    show_hazardous_only = request.GET.get('hazardous', '') == '1'
    
    # Загружаем данные с NASA API, если их нет за текущую неделю
    week_flybys = Flyby.objects.filter(
        date__date__gte=today,
        date__date__lte=week_end
    )
    
    if not week_flybys.exists():
        # Загружаем данные с NASA API
        data = NASANeoWsService.fetch_week_data(today, week_end)
        if data:
            NASANeoWsService.process_and_save_data(data)
            messages.success(request, 'Данные успешно загружены с NASA API')
        else:
            messages.warning(request, 'Не удалось загрузить данные с NASA API')
    
    # Получаем сближения с информацией об астероидах
    flybys = Flyby.objects.select_related('asteroid').filter(
        date__date__gte=today,
        date__date__lte=week_end
    ).order_by('date')
    
    # Фильтрация по опасным объектам
    if show_hazardous_only:
        flybys = flybys.filter(asteroid__is_potentially_hazardous=True)
    
    # Статистика для графика
    total_asteroids = Asteroid.objects.filter(
        flybys__date__date__gte=today,
        flybys__date__date__lte=week_end
    ).distinct().count()
    
    hazardous_count = Asteroid.objects.filter(
        flybys__date__date__gte=today,
        flybys__date__date__lte=week_end,
        is_potentially_hazardous=True
    ).distinct().count()
    
    safe_count = total_asteroids - hazardous_count
    
    # Проверяем, какие астероиды уже в watchlist пользователя
    user_watchlist_ids = set()
    if request.user.is_authenticated:
        user_watchlist_ids = set(
            Watchlist.objects.filter(user=request.user)
            .values_list('asteroid_id', flat=True)
        )
    
    context = {
        'flybys': flybys,
        'show_hazardous_only': show_hazardous_only,
        'total_asteroids': total_asteroids,
        'hazardous_count': hazardous_count,
        'safe_count': safe_count,
        'user_watchlist_ids': user_watchlist_ids,
        'week_start': today,
        'week_end': week_end,
    }
    
    return render(request, 'core/index.html', context)


@login_required
def watchlist(request):
    """Личный кабинет - список отслеживания пользователя."""
    # Получаем фильтр для потенциально опасных объектов
    show_hazardous_only = request.GET.get('hazardous', '') == '1'
    
    # Получаем элементы watchlist пользователя
    watchlist_items = Watchlist.objects.filter(
        user=request.user
    ).select_related('asteroid').order_by('-added_at')
    
    # Фильтрация по опасным объектам
    if show_hazardous_only:
        watchlist_items = watchlist_items.filter(
            asteroid__is_potentially_hazardous=True
        )
    
    # Получаем ближайшие сближения для астероидов из watchlist
    today = timezone.now()
    week_end = today + timedelta(days=30)
    
    watchlist_asteroid_ids = watchlist_items.values_list('asteroid_id', flat=True)
    upcoming_flybys = Flyby.objects.filter(
        asteroid_id__in=watchlist_asteroid_ids,
        date__gte=today,
        date__lte=week_end
    ).select_related('asteroid').order_by('date')
    
    context = {
        'watchlist_items': watchlist_items,
        'upcoming_flybys': upcoming_flybys,
        'show_hazardous_only': show_hazardous_only,
    }
    
    return render(request, 'core/watchlist.html', context)


@login_required
def add_to_watchlist(request, asteroid_id):
    """Добавляет астероид в список отслеживания пользователя."""
    asteroid = get_object_or_404(Asteroid, id=asteroid_id)
    
    watchlist_item, created = Watchlist.objects.get_or_create(
        user=request.user,
        asteroid=asteroid
    )
    
    if created:
        messages.success(request, f'Астероид {asteroid.name} добавлен в список отслеживания')
    else:
        messages.info(request, f'Астероид {asteroid.name} уже в списке отслеживания')
    
    return redirect('index')


@login_required
def remove_from_watchlist(request, watchlist_id):
    """Удаляет астероид из списка отслеживания пользователя."""
    watchlist_item = get_object_or_404(
        Watchlist,
        id=watchlist_id,
        user=request.user
    )
    
    asteroid_name = watchlist_item.asteroid.name
    watchlist_item.delete()
    
    messages.success(request, f'Астероид {asteroid_name} удалён из списка отслеживания')
    return redirect('watchlist')


@login_required
def update_watchlist_notes(request, watchlist_id):
    """Обновляет заметки пользователя для элемента watchlist."""
    watchlist_item = get_object_or_404(
        Watchlist,
        id=watchlist_id,
        user=request.user
    )
    
    if request.method == 'POST':
        watchlist_item.user_notes = request.POST.get('user_notes', '')
        watchlist_item.save()
        messages.success(request, 'Заметки обновлены')
        return redirect('watchlist')
    
    return redirect('watchlist')

