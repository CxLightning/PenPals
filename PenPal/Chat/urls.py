from django.urls import path, reverse
from . import views

urlpatterns = [
    #Home and Main Pages
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),

    #Language select and Partner Matching
    path('language/', views.language_select, name='language_select'),
    path('language/<int:language_id>/partners/', views.partner_list, name='partner_list'),
    path('start-chat/<int:partner_id>/<int:language_id>/', views.start_chat, name='start_chat'),

    # Chat Room
    path('chat/<int:room_id>/', views.chat_room, name='chat_room'),
    path('my-chats/', views.my_chats, name='my_chats'),

    #User Profile
    path('profile/', views.profile, name='profile'),
    path('profile/<int:user_id>/', views.user_profile, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    #Settings
    path('settings/', views.settings_view, name='settings'),

    #Authentication
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
