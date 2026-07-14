from django.urls import path

from .views import CartPageView, CoursesPageView, HomePageView, ServicesPageView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('courses/', CoursesPageView.as_view(), name='courses'),
    path('cart/', CartPageView.as_view(), name='cart'),
    path('services/', ServicesPageView.as_view(), name='services'),
]
