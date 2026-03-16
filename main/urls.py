from django.urls import path
from . import views

urlpatterns = [
    # API endpoints
    path('api/get_statistik1', views.api_get_statistik1, name='api_get_statistik1'),
    path('api/get_statistik', views.api_get_statistik, name='api_get_statistik'),
    path('api/get_question', views.api_get_question, name='api_get_question'),
    path('api/submit_answer', views.api_submit_answer, name='api_submit_answer'),
    path('api/signup', views.api_signup, name='api_signup'),
    path('api/signin', views.api_signin, name='api_signin'),
    path('api/check_auth', views.api_check_auth, name='api_check_auth'),
    path('api/logout', views.api_logout, name='api_logout'),
    path('api/profile', views.api_profile, name='api_profile'),
    path('api/csrf', views.get_csrf_token, name='csrf_token'),
    path('api/restart_game', views.api_restart_game, name='api_restart_game'),
    path('api/get_rating', views.api_get_rating, name='api_get_rating'),
    path('api/get_rating_top3', views.api_get_rating_top3, name='api_get_rating_top3'),
    # Page views
    path('', views.home_page, name='home_page'),
    path('question/', views.question_page, name='question_page'),
    path('rating/', views.rating_page, name='rating_page'),
    path('signin/', views.signin_page, name='signin_page'),
    path('signup/', views.signup_page, name='signup_page'),
]