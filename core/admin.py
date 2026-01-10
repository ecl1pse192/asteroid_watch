from django.contrib import admin
from .models import Asteroid, Flyby, Watchlist


@admin.register(Asteroid)
class AsteroidAdmin(admin.ModelAdmin):
    list_display = ('name', 'nasa_id', 'is_potentially_hazardous', 'absolute_magnitude', 'created_at')
    list_filter = ('is_potentially_hazardous', 'created_at')
    search_fields = ('name', 'nasa_id')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Flyby)
class FlybyAdmin(admin.ModelAdmin):
    list_display = ('asteroid', 'date', 'velocity_kmh', 'miss_distance_km', 'created_at')
    list_filter = ('date', 'created_at', 'asteroid__is_potentially_hazardous')
    search_fields = ('asteroid__name', 'asteroid__nasa_id')
    date_hierarchy = 'date'
    readonly_fields = ('created_at',)


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'asteroid', 'added_at')
    list_filter = ('added_at', 'asteroid__is_potentially_hazardous')
    search_fields = ('user__username', 'asteroid__name', 'user_notes')
    readonly_fields = ('added_at',)
