from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, login, password=None, **extra_fields):
        if not login:
            raise ValueError('Логин должен быть указан')
        user = self.model(login=login, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, login, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(login, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    login = models.CharField(max_length=50, unique=True, verbose_name='Логин')
    password_hash = models.CharField(max_length=255, verbose_name='Хэш пароля')
    name = models.CharField(max_length=50, verbose_name='Имя')
    surname = models.CharField(max_length=50, verbose_name='Фамилия')
    user_class = models.CharField(max_length=10, verbose_name='Класс', db_column='класс')
    role = models.CharField(max_length=20, default='user', verbose_name='Роль')
    study = models.IntegerField(default=0, verbose_name='Учеба', db_column='учеба')
    fun = models.IntegerField(default=0, verbose_name='Развлечения', db_column='развлечения')
    health = models.IntegerField(default=0, verbose_name='Здоровье', db_column='здоровье')
    points = models.IntegerField(default=0, verbose_name='Количество очков', db_column='количество_очков')
    registration_date = models.DateTimeField(default=timezone.now, verbose_name='Дата регистрации', db_column='дата_регистрации')
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'login'
    REQUIRED_FIELDS = ['name', 'surname', 'user_class']
    
    class Meta:
        db_table = 'Пользователь'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    def __str__(self):
        return f"{self.name} {self.surname}"
    
    def get_full_name(self):
        return f"{self.name} {self.surname}"
    
    def get_short_name(self):
        return self.name
    
    @property
    def current_level(self):
        return self.points // 100 + 1
    
    @property
    def current_level_points(self):
        return self.points % 100
    
    @property
    def max_level_points(self):
        return self.current_level * 100
    
    @property
    def progress_percentage(self):
        return (self.current_level_points / 100) * 100 if self.max_level_points > 0 else 0


class Category(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название', db_column='название')
    
    class Meta:
        db_table = 'Категория'
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
    
    def __str__(self):
        return self.name


class Question(models.Model):
    text = models.TextField(verbose_name='Текст вопроса', db_column='текст')
    creation_date = models.DateTimeField(default=timezone.now, verbose_name='Дата создания', db_column='дата_создания')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория', db_column='id_категории')
    
    class Meta:
        db_table = 'Вопросы'
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'
    
    def __str__(self):
        return self.text[:50]


class AnswerOption(models.Model):
    text = models.TextField(verbose_name='Текст ответа', db_column='текст_ответа')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='Вопрос', db_column='id_вопроса')
    study_change = models.IntegerField(verbose_name='Изменение учебы', db_column='изм_учеба')
    fun_change = models.IntegerField(verbose_name='Изменение развлечений', db_column='изм_развлечения')
    health_change = models.IntegerField(verbose_name='Изменение здоровья', db_column='изм_здоровья')
    
    class Meta:
        db_table = 'Вариант_ответа'
        verbose_name = 'Вариант ответа'
        verbose_name_plural = 'Варианты ответов'
    
    def __str__(self):
        return self.text[:50]


class ActionLog(models.Model):
    event_date = models.DateTimeField(default=timezone.now, verbose_name='Дата события', db_column='дата_события')
    action_name = models.CharField(max_length=255, verbose_name='Наименование действия', db_column='наименование_действия')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь', db_column='Пользователь_id')
    
    class Meta:
        db_table = 'Логи_действий'
        verbose_name = 'Лог действия'
        verbose_name_plural = 'Логи действий'
    
    def __str__(self):
        return f"{self.event_date} - {self.action_name}"