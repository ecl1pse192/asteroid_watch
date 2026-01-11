from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('watchlist/', views.watchlist, name='watchlist'),
    path('watchlist/add/<int:asteroid_id>/', views.add_to_watchlist, name='add_to_watchlist'),
    path('watchlist/remove/<int:watchlist_id>/', views.remove_from_watchlist, name='remove_from_watchlist'),
    path('watchlist/update-notes/<int:watchlist_id>/', views.update_watchlist_notes, name='update_watchlist_notes'),
]
