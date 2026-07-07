from django.views.generic import TemplateView

class HomePageView(TemplateView):
    template_name = 'home.html'


class CoursesPageView(TemplateView):
    template_name = 'courses.html'
