from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Language, UserProfile, ChatRoom, Message
from .utils  import (find_language_partners, calculate_match_score, get_or_create_chat_room, get_user_chat_rooms, mark_messages_as_read)

# Create your views here.

