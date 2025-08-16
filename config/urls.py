from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from apps.auth_user.views import router as auth_router

api = NinjaAPI()
api.add_router("/auth/", auth_router)

@api.get("/hello")
def hello(request):
    return {"message": "Hello from Djan1go Ninja"}

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", api.urls),
]
