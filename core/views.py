from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Asteroid, Flyby, Watchlist


def index(request):
    """
    Главная страница.
    Показывает список астероидов из базы данных.
    Данные обновляются через команду: python manage.py load_nasa
    """
    today = timezone.now().date()
    week_end = today + timedelta(days=7)

    show_hazardous_only = request.GET.get('hazardous', '') == '1'
  
    flybys = Flyby.objects.select_related('asteroid').filter(
        date__gte=today,
        date__lte=week_end
    ).order_by('date')

    if show_hazardous_only:
        flybys = flybys.filter(asteroid__is_potentially_hazardous=True)
    
    week_asteroids_qs = Asteroid.objects.filter(
        flybys__date__gte=today,
        flybys__date__lte=week_end
    ).distinct()

    total_asteroids = week_asteroids_qs.count()
    hazardous_count = week_asteroids_qs.filter(is_potentially_hazardous=True).count()
    safe_count = total_asteroids - hazardous_count
    
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
    """Личный кабинет: список отслеживания."""
    show_hazardous_only = request.GET.get('hazardous', '') == '1'
    
    watchlist_items = Watchlist.objects.filter(
        user=request.user
    ).select_related('asteroid').order_by('-added_at')
    
    if show_hazardous_only:
        watchlist_items = watchlist_items.filter(
            asteroid__is_potentially_hazardous=True
        )
    
    today = timezone.now().date()
    month_end = today + timedelta(days=30)
    
    watchlist_asteroid_ids = watchlist_items.values_list('asteroid_id', flat=True)
    
    upcoming_flybys = Flyby.objects.filter(
        asteroid_id__in=watchlist_asteroid_ids,
        date__gte=today,
        date__lte=month_end
    ).select_related('asteroid').order_by('date')
    
    context = {
        'watchlist_items': watchlist_items,
        'upcoming_flybys': upcoming_flybys,
        'show_hazardous_only': show_hazardous_only,
    }
    
    return render(request, 'core/watchlist.html', context)


@login_required
def add_to_watchlist(request, asteroid_id):
    """Добавить в избранное."""
    asteroid = get_object_or_404(Asteroid, id=asteroid_id)
    
    obj, created = Watchlist.objects.get_or_create(
        user=request.user,
        asteroid=asteroid
    )
    
    if created:
        messages.success(request, f'{asteroid.name} добавлен в наблюдение.')
    else:
        messages.info(request, f'{asteroid.name} уже отслеживается.')
    
    return redirect(request.META.get('HTTP_REFERER', 'index'))


@login_required
def remove_from_watchlist(request, watchlist_id):
    """Удалить из избранного."""
    item = get_object_or_404(Watchlist, id=watchlist_id, user=request.user)
    name = item.asteroid.name
    item.delete()
    
    messages.success(request, f'{name} удален из списка.')
    return redirect('watchlist')


@login_required
def update_watchlist_notes(request, watchlist_id):
    """Обновить заметку."""
    item = get_object_or_404(Watchlist, id=watchlist_id, user=request.user)
    
    if request.method == 'POST':
        item.user_notes = request.POST.get('user_notes', '')
        item.save()
        messages.success(request, 'Заметка сохранена')
        
    return redirect('watchlist')
