from django.urls import path

from . import views

urlpatterns = [
    path("search/", views.search_pokemon, name="pokemon-search"),
    path("", views.list_pokemon, name="pokemon-list"),
    path("<str:identifier>/", views.pokemon_detail, name="pokemon-detail"),
]
