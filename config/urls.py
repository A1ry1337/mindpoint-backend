from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI

from apps.assessments.dass.views import router as dass9_router
from apps.auth_user.views import router as auth_router
from apps.manager.management.views import router as management_router

api = NinjaAPI()
api.add_router("/auth/", auth_router)
api.add_router("/dass9/", dass9_router)
api.add_router("/management/", management_router)
urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", api.urls),
]
