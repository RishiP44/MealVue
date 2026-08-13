from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('analyze/', views.analyze_shelf, name='analyze_shelf'),
    path('match/', views.match_correction, name='match_correction'),
    path('library/', views.library_books, name='library_books'),
]
