from django.urls import path

from .views import CoursesPageView, HomePageView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('courses/', CoursesPageView.as_view(), name='courses'),
]
