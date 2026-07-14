from django.views.generic import TemplateView


class HomePageView(TemplateView):
    template_name = 'home.html'


class CoursesPageView(TemplateView):
    template_name = 'courses.html'


class CartPageView(TemplateView):
    template_name = 'cart.html'


class ServicesPageView(TemplateView):
    template_name = 'services.html'
