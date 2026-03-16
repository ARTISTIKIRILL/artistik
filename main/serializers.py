from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import User, Question, AnswerOption


class UserSerializer(serializers.ModelSerializer):
    current_level = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'login', 'name', 'surname', 'user_class', 'role', 
                  'study', 'fun', 'health', 'points', 'current_level']
        read_only_fields = ['id', 'role', 'points', 'study', 'fun', 'health']
    
    def get_current_level(self, obj):
        """Получение текущего уровня пользователя"""
        return (obj.points // 100) + 1 if obj.points else 1


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    current_level = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'login', 'name', 'surname', 'full_name', 'user_class', 
                  'role', 'study', 'fun', 'health', 'points', 'current_level']
        read_only_fields = ['id', 'role', 'points', 'study', 'fun', 'health']
    
    def get_full_name(self, obj):
        return f"{obj.name} {obj.surname}"
    
    def get_current_level(self, obj):
        """Получение текущего уровня пользователя"""
        return (obj.points // 100) + 1 if obj.points else 1


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['login', 'password', 'password2', 'name', 'surname', 'user_class']
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        
        # Проверка уникальности логина
        if User.objects.filter(login=data['login']).exists():
            raise serializers.ValidationError({"login": "Пользователь с таким логином уже существует"})
        
        return data
    
    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        
        # Используем правильный менеджер для создания пользователя
        user = User.objects.create_user(
            login=validated_data['login'],
            password=password,
            name=validated_data.get('name', ''),
            surname=validated_data.get('surname', ''),
            user_class=validated_data.get('user_class', '')
        )
        return user


class LoginSerializer(serializers.Serializer):
    login = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    def validate(self, data):
        login = data.get('login')
        password = data.get('password')
        
        if login and password:
            user = authenticate(username=login, password=password)
            
            if user:
                if not user.is_active:
                    raise serializers.ValidationError("Пользователь деактивирован")
                return user
            else:
                raise serializers.ValidationError("Неверный логин или пароль")
        else:
            raise serializers.ValidationError("Необходимо указать логин и пароль")


class AnswerOptionSerializer(serializers.ModelSerializer):
    letter = serializers.SerializerMethodField()
    effects = serializers.SerializerMethodField()
    
    class Meta:
        model = AnswerOption
        fields = ['id', 'text', 'letter', 'effects']
    
    def get_letter(self, obj):
        # Получаем индекс ответа в вопросе и преобразуем в букву
        try:
            options = list(obj.question.answeroption_set.all().order_by('id'))
            index = options.index(obj)
            return chr(index + 65)  # A, B, C, D, ...
        except (ValueError, AttributeError):
            return '?'
    
    def get_effects(self, obj):
        return {
            'study': obj.study_change,
            'fun': obj.fun_change,
            'health': obj.health_change
        }


class QuestionSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'text', 'category']


class QuestionDetailSerializer(serializers.ModelSerializer):
    question = serializers.SerializerMethodField()
    options = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = ['question', 'options']
    
    def get_question(self, obj):
        return {
            'id': obj.id,
            'text': obj.text,
            'category': obj.category.name if obj.category else None
        }
    
    def get_options(self, obj):
        options = obj.answeroption_set.all().order_by('id')
        return AnswerOptionSerializer(options, many=True).data


class StatistikSerializer(serializers.Serializer):
    """Сериализатор для статистики пользователя"""
    user = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()
    
    def get_user(self, obj):
        """Получение данных пользователя"""
        return {
            'id': obj.id,
            'name': obj.name,
            'surname': obj.surname,
            'user_class': obj.user_class,
            'login': obj.login
        }
    
    def get_level(self, obj):
        """Получение данных об уровне"""
        points = obj.points
        current_level = (points // 100) + 1
        cur_level_points = points % 100
        max_level_points = current_level * 100
        progress_percentage = (cur_level_points / 100) * 100 if max_level_points > 0 else 0
        
        return {
            'current_level': current_level,
            'points': points,
            'cur_level_points': cur_level_points,
            'max_level_points': max_level_points,
            'progress_percentage': progress_percentage,
        }
    
    def get_stats(self, obj):
        """Получение характеристик"""
        return {
            'study': max(0, min(100, getattr(obj, 'study', 0))),
            'fun': max(0, min(100, getattr(obj, 'fun', 0))),
            'health': max(0, min(100, getattr(obj, 'health', 0))),
        }