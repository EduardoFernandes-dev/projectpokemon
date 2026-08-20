from django.contrib import admin
from django.urls import include, path

from pokemon import views as pokemon_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/pokemon/", include("pokemon.urls")),
    path("api/types/", pokemon_views.type_list, name="type-list"),
    path("api/generations/", pokemon_views.generation_list, name="generation-list"),
    path("api/tms/", pokemon_views.tm_list, name="tm-list"),
    path("api/moves/<str:identifier>/", pokemon_views.move_detail, name="move-detail"),
]
