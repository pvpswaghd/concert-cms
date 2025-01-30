from django.urls import path
from . import views

# Starting path: http://localhost:8000/api/
urlpatterns = [
    path("create-concert/", views.create_concert, name="create_concert"),
    path("update-concert/<int:concert_id>/", views.update_concert, name="update_concert"),
    path("remove-concert/<int:concert_id>/", views.remove_concert, name="delete_concert"),
]