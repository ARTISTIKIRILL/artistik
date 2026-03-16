import random
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
from django.core import serializers
import json

from .models import User, Question, AnswerOption, ActionLog
from .decorators import login_required_api, login_required_web
from .serializers import (
    UserSerializer, UserProfileSerializer, RegisterSerializer,
    LoginSerializer, QuestionDetailSerializer, StatistikSerializer
)


# API Views
@require_http_methods(["GET"])
def api_get_statistik1(request):
    """Заглушка для тестирования"""
    test_data = {
        "user": {
            "id": 12345,
            "name": "Мария",
            "surname": "Петрова",
            "user_class": "11Б",
            "login": "petrova_maria"
        },
        "level": {
            "current_level": 4,
            "points": 342,
            "cur_level_points": 42,
            "max_level_points": 400,
            "progress_percentage": 42.0,
        }, 
        "stats": {
            "study": 78,
            "fun": 65,
            "health": 92
        }
    }
    return JsonResponse(test_data)


@require_http_methods(["GET"])
@login_required_api
def api_get_statistik(request):
    try:
        serializer = StatistikSerializer(request.user)
        return JsonResponse(serializer.data)
    except Exception as e:
        print(str(e))
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
@login_required_api
def api_get_question(request):
    try:
        # Получаем случайный вопрос
        question = Question.objects.order_by('?').first()
        
        if not question:
            return JsonResponse({"error": "Вопросы не найдены"}, status=404)
        
        serializer = QuestionDetailSerializer(question)
        return JsonResponse(serializer.data)
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["POST"])
@login_required_api
@transaction.atomic
def api_submit_answer(request):
    try:
        data = json.loads(request.body)
        answer_id = data.get('answer_id')
        question_id = data.get('question_id')
        
        if not answer_id or not question_id:
            return JsonResponse({"error": "Заполните все поля"}, status=400)
        
        # Получаем ответ
        answer = get_object_or_404(AnswerOption, id=answer_id, question_id=question_id)
        
        points = 20
        
        # Обновляем пользователя с защитой от отрицательных значений
        user = request.user
        
        # Обновляем очки (они могут уходить в минус? если нет - оставляем как есть)
        user.points += points
        
        # Обновляем характеристики с проверкой на отрицательные значения
        # user.study = max(0, user.study + answer.study_change)
        # user.fun = max(0, user.fun + answer.fun_change)
        # user.health = max(0, user.health + answer.health_change)
        
        user.study = min(100, max(0, user.study + answer.study_change))
        user.fun = min(100, max(0, user.fun + answer.fun_change))
        user.health = min(100, max(0, user.health + answer.health_change))
        
        user.save()
        
        # Логируем действие
        ActionLog.objects.create(
            event_date=timezone.now(),
            action_name="Ответ на вопрос",
            user=user
        )
        
        # Обновляем сессию пользователя
        login(request, user)
        
        # Возвращаем актуальные значения характеристик
        return JsonResponse({
            "message": "Ответ принят",
            "points_earned": points,
            "effects": {
                "study": answer.study_change,
                "fun": answer.fun_change,
                "health": answer.health_change,
            },
            "current_stats": {
                "study": user.study,
                "fun": user.fun,
                "health": user.health,
                "points": user.points
            }
        })
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["POST"])
def api_signup(request):
    try:
        data = json.loads(request.body)
        
        # Переименуйте переменную с login на username или login_field
        username = data.get('login')  # вместо login
        password = data.get('password')
        password2 = data.get('password2')
        name = data.get('name')
        surname = data.get('surname')
        user_class = data.get('user_class')
        
        # Валидация
        if not all([username, password, name, surname, user_class]):
            return JsonResponse({"error": "Не все поля заполнены"}, status=400)
        
        if password != password2:
            return JsonResponse({"error": "Пароли не совпадают"}, status=400)
        
        if len(password) < 8:
            return JsonResponse({"error": "Пароль должен быть не менее 8 символов"}, status=400)
        
        # Проверка существования пользователя
        if User.objects.filter(login=username).exists():  # используем username
            return JsonResponse({"error": "Логин уже существует"}, status=409)
        
        # Создание пользователя - используем username
        user = User.objects.create_user(
            login=username,  # передаём username как login
            password=password,
            name=name,
            surname=surname,
            user_class=user_class,
            registration_date=timezone.now()
        )
        
        return JsonResponse({"message": "Регистрация успешна"}, status=201)
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["POST"])
def api_signin(request):
    try:
        data = json.loads(request.body)
        serializer = LoginSerializer(data=data)
        
        if serializer.is_valid():
            user = serializer.validated_data
            login(request, user)
            
            user_serializer = UserSerializer(user)
            
            return JsonResponse({
                "message": "Успешный вход",
                "user": user_serializer.data
            })
        
        return JsonResponse({"error": "Неверный логин или пароль"}, status=401)
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def api_check_auth(request):
    if request.user.is_authenticated:
        serializer = UserSerializer(request.user)
        return JsonResponse({
            "authenticated": True,
            "user": serializer.data
        })
    return JsonResponse({"authenticated": False})


@require_http_methods(["POST"])
@login_required_api
def api_logout(request):
    logout(request)
    return JsonResponse({"message": "Вы успешно вышли из аккаунта"})


@require_http_methods(["GET"])
@login_required_api
def api_profile(request):
    serializer = UserProfileSerializer(request.user)
    return JsonResponse(serializer.data)

@require_http_methods(["POST"])
@login_required_api
@transaction.atomic
def api_restart_game(request):
    """
    Эндпоинт для рестарта игры:
    - Вычитает 30 очков
    - Устанавливает все характеристики в 40
    """
    try:
        user = request.user
        
        # Вычитаем 30 очков (но не ниже 0)
        user.points = max(0, user.points - 120)
        
        # Устанавливаем все характеристики в 40
        user.study = 40
        user.fun = 40
        user.health = 40
        
        user.save()
        
        # Логируем действие
        ActionLog.objects.create(
            event_date=timezone.now(),
            action_name="Рестарт игры (характеристики обнулились)",
            user=user
        )
        
        # Обновляем сессию пользователя
        login(request, user)
        
        return JsonResponse({
            "message": "Игра перезапущена",
            "points": user.points,
            "stats": {
                "study": user.study,
                "fun": user.fun,
                "health": user.health
            }
        })
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

from django.db.models import F

@require_http_methods(["GET"])
def api_get_rating(request):
    """
    Эндпоинт для получения рейтинга пользователей
    """
    try:
        # Получаем всех пользователей, сортируем по очкам (убывание)
        users = User.objects.all().order_by('-points')[:100]  # Ограничиваем 100 пользователями
        
        rating_data = []
        for position, user in enumerate(users, start=1):
            # Вычисляем уровень
            level = (user.points // 100) + 1
            
            rating_data.append({
                'position': position,
                'user_id': user.id,
                'name': user.name,
                'surname': user.surname,
                'full_name': f"{user.name} {user.surname}",
                'login': user.login,
                'user_class': user.user_class,
                'points': user.points,
                'level': level,
                'study': user.study,
                'fun': user.fun,
                'health': user.health,
                'avatar_initials': (user.name[0] if user.name else '') + (user.surname[0] if user.surname else ''),
            })
        
        return JsonResponse({
            'users': rating_data,
            'total_count': len(rating_data)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_get_rating_top3(request):
    """
    Эндпоинт для получения топ-3 пользователей
    """
    try:
        top_users = User.objects.all().order_by('-points')[:3]
        
        top_data = []
        for position, user in enumerate(top_users, start=1):
            top_data.append({
                'position': position,
                'name': user.name,
                'surname': user.surname,
                'full_name': f"{user.name} {user.surname}",
                'user_class': user.user_class,
                'points': user.points,
                'level': (user.points // 100) + 1,
                'avatar_initials': (user.name[0] if user.name else '') + (user.surname[0] if user.surname else ''),
            })
        
        return JsonResponse({'top_users': top_data})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
        
# HTML Page Views
def home_page(request):
    return render(request, 'index.html')


def question_page(request):
    return render(request, 'question.html')


def rating_page(request):
    return render(request, 'rating.html')


def signin_page(request):
    if request.user.is_authenticated:
        return redirect('home_page')
    return render(request, 'signin.html')


def signup_page(request):
    if request.user.is_authenticated:
        return redirect('home_page')
    return render(request, 'signup.html')


@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({'csrfToken': request.META.get('CSRF_COOKIE', '')})