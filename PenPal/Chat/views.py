from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Language, UserProfile, ChatRoom, Message
from .utils  import (find_lang_partners, match_score, get_or_create_chatroom, get_user_chatrooms, mark_message_as_read)

# Create your views here.


# Home & Dashboard

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    total_users = User.objects.count()
    total_languages = Language.objects.count()
    total_messages = Message.objects.count()

    context = {
        'total_users': total_users,
        'total_languages': total_languages,
        'total_messages': total_messages,
    }
    return render(request,'chat/home.html', context)


@login_required
def dashboard(request):
    user_profile = request.user.userprofile

    chat_rooms = get_user_chatrooms(request.user),

    learning_languages = user_profile.learn_lang.all()

    days_active = (timezone.now().date() - request.user.date_joined.date()).days

    message_count = Message.objects.filter(sender=request.user).count()

    context = {
        'user_profile': user_profile,
        'chat_rooms': chat_rooms[:5],
        'learning_languages': learning_languages,
        'days_active': days_active,
        'message_count': message_count,
    }
    return render(request,'chat/dashboard.html', context)

# Language and Partner Matching

@login_required
def language_select(request):
    languages = Language.objects.annotate(learner_count=Count('learners')).all()

    user_profile = request.user.userprofile
    user_learning = user_profile.learn_lang.all()

    context = {
        'languages': languages,
        'user_learning': user_learning,
    }
    return render(request,'chat/language_select.html', context)

@login_required
def partner_list(request, language_id):
    language = get_object_or_404(Language, id=language_id)

    # to find potential match
    partners = find_lang_partners(request.user, language)

    partners_with_scores = []
    for partner in partners:
        score = match_score(request.user.userprofile, partner)
        partners_with_scores.append({
            'profile': partner,
            'score':score,})

    # Sort by score
    partners_with_scores.sort(key=lambda x: x['score'], reverse=True)
    context = {
        'language': language,
        'partners_with_scores': partners_with_scores[:20],
    }
    return render(request,'chat/partner_list.html', context)

@login_required
def start_chat(request, partner_id, language_id):
    language = get_object_or_404(Language, id=language_id)
    partner = get_object_or_404(Language, id=partner_id)

    # prevent just one person messaging them selves
    if partner == request.user:
        messages.error(request,'It Takes Two to have a conversation!')
        return redirect('language_select')

    chat_room = get_or_create_chatroom(request.user, partner, language)

    messages.success(request, f'Chat started with {partner.username}!')
    return redirect('language_select')

# Chat Functions

@login_required
def chat_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)

    # Verify user
    if request.user not in room.people.all():
        messages.error(request,'Wrong room try another one!')
        return redirect('my_chats')

    chat_messages = room.messages.select_related('sender').all()

    mark_message_as_read(room, request.user)

    other_user = room.get_other_people(request.user)

    context = {
        'room': room,
        'other_user': other_user,
        'messages': chat_messages,
    }
    return render(request,'chat/chat_room.html', context)

@login_required
def my_chats(request):
    chat_rooms = get_user_chatrooms(request.user)

    total_unread = sum(room['unread_count'] for room in chat_rooms)

    context = {
        'chat_rooms': chat_rooms,
        'total_unread': total_unread,
    }
    return render(request,'chat/my_chats.html', context)


# User Profile

@login_required
def profile(request):
    return render('user_profile', username=request.user.username)

@login_required
def user_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    user_profile = profile.user.userprofile

    #check if viewing own profile
    is_own_profile = (request.user == profile_user)

    #Stats
    chat_count = ChatRoom.objects.filter(people=profile_user).count()
    messages_count = Message.objects.filter(sender=profile_user).count()
    days_active = (timezone.now().date() - profile_user.date_joined.date()).days

    # Get Learning languages
    learning_languages = user_profile.learn_lang.all()

    context = {
        'profile_user': profile_user,
        'user_profile': user_profile,
        'is_own_profile': is_own_profile,
        'chat_count': chat_count,
        'messages_count': messages_count,
        'days_active': days_active,
        'learning_languages': learning_languages,
    }
    return render(request,'chat/profile.html', context)

# Edit profile

@login_required
def edit_profile(request):
    user_profile = request.user.userprofile

    if request.method == 'POST':
        #Update user info
        request.user.userprofile.first_name = request.POST('first_name','')
        request.user.userprofile.last_name = request.POST('last_name','')
        request.user.email = request.POST('email','')
        request.user.save()

        #Update profile info
        user_profile.bio = request.POST('bio','')
        user_profile.pro_level = request.POST('pro_level','beginner')

        #Handle Native Language
        native_lang_id = request.POST('native_language')
        if native_lang_id:
            user_profile.native_language = Language.objects.get(id=native_lang_id)

        learning_lang_ids = request.POST('learning_language')
        user_profile.learn_lang.clear()
        for lang_id in learning_lang_ids:
            language = language.objects.filter(id=lang_id)
            user_profile.learn_lang.add(language)

        user_profile.save()

        messages.success(request, 'Profile Updated')
        return redirect('profile')

    all_languages = Language.objects.all()
    context = {
        'all_languages': all_languages,
        'user_profile': user_profile,
    }
    return render(request,'chat/edit_profile.html', context)

# Settings

@login_required
def settings_view(request):
    user_profile = request.user.userprofile

    if request.method == 'POST':
        user_profile.is_available = request.POST('is_available') == 'on'
        user_profile.save()

        messages.success(request, 'Settings Updated')
        return redirect('settings')
    context = {
        'user_profile': user_profile,
    }
    return render(request,'chat/settings.html', context)


#Authentication

def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST('username')
        email = request.POST('email')
        password = request.POST('password')
        password_confirm = request.POST('password_confirm')
        first_name = request.POST('first_name', '')
        last_name = request.POST('last_name', '')

        #Validation
        if not all([username, email, password, password_confirm]):
            messages.error(request, 'Please fill all fields')
            return redirect(request, 'registration/signup.html')

        if password != password_confirm:
            messages.error(request, 'Passwords do not match')
            return redirect(request, 'registration/signup.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect(request, 'registration/signup.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect(request, 'registration/signup.html')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # set inital info if provided
        native_lang_id = request.POST('native_language')
        if native_lang_id:
            user.native_language = Language.objects.get(id=native_lang_id)
            user.save()

        login(request, user)
        messages.success(request, f'Welcome to PenPal, {username}')
        return redirect('language_select')

    langauges = Language.objects.all()
    context = {
        'langauges': langauges,
    }
    return render(request, 'registration/signup.html', context)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST('username')
        password = request.POST('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back , {username}')

            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid Username or Password')

    return render(request, 'registration/login.html')

@login_required
def logout_view(request):
    username = request.user.username
    logout(request)
    messages.success(request, f'See ya Pal')
    return redirect('home')
