from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI

from apps.assessments.dass.views import router as dass9_router
from apps.assessments.mood.views import router as mood_router
from apps.auth_user.views import router as auth_router
from apps.manager.management.views import router as management_router
from apps.analytics.dass_analytics.views import router as dass_analytics_router
from apps.analytics.user_dass_analytics.views import router as user_dass_analytics_router
from apps.analytics.user_mood_analytics.views import router as user_mood_analytics_router
from apps.analytics.mood_analytics.views import router as mood_analytics_router
from apps.employee.settings.views import router as employee_settings_router

api = NinjaAPI()
api.add_router("/auth/", auth_router)
api.add_router("/dass9/", dass9_router)
api.add_router("/mood/", mood_router)
api.add_router("/management/", management_router)
api.add_router("/dass_analytics/", dass_analytics_router)
api.add_router("/user_dass_analytics/", user_dass_analytics_router)
api.add_router("/user_mood_analytics/", user_mood_analytics_router)
api.add_router("/mood_analytics/", mood_analytics_router)
api.add_router("/employee_settings/", employee_settings_router)
urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", api.urls),
]
