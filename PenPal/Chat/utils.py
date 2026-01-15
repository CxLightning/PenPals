from django.db.models import Q
from .models import UserProfile, ChatRoom, Message


#ABV native_lang = native_language, Learn_lang = Learning_language
#Creating functions to help with matching for user experience., along with the function of message is read and the ability to create rooms if one is not created.
#Ideal Match: is a Language exchange, User wants to learn language X, partner is native in X and wants to Learn user's native language(language Exchange),
# Will also use a score to help the function find matches based on profile

def find_lang_partners(user, language):
    try:
        user_profile = user.userprofile
    except UserProfile.DoesNotExist:
        return UserProfile.objects.none()

    ideal_matches = UserProfile.objects.filter(
        native_lang=language,
        learn_lang=user_profile.native_lang,
        is_availble=True
    ).exclude(user=user).select_related('user', ' native_lang')

    if not ideal_matches.exists():
        broader_matches = UserProfile.objects.filter(
            Q(native_lang=language) | Q(learn_lang=language),
            is_availble=True
        ).exclude(user=user).select_related('user', ' native_lang')
        return broader_matches

    return ideal_matches


def match_score(user_profile, partner_profile):
    score = 0
    if (partner_profile.native_lang in user_profile.learn_lang.all() and
    user_profile.native_lang in partner_profile.learn_lang.all()):
        score += 50

    if user_profile.pro_level == partner_profile.pro_level:
        score += 20

    if user_profile.is_availble and partner_profile.is_availble:
        score += 15

    if partner_profile.bio:
        score += 10

    message_count = Message.objects.filter(sender=partner_profile.user).count()
    if message_count > 0:
        score += 5

    return min(score, 100)


def get_or_create_chatroom(user1, user2, language):
    existing_room = ChatRoom.objects.filter(
        people = user1,
        language = language,
    ).filter(
        people=user2,
    ).first()
    if existing_room:
        return existing_room

    room_name = f'{language.name}: {user1.username} & {user2.username}'
    new_room = ChatRoom.objects.create(
        name=room_name,
        language=language
    )
    new_room.people.add(user1, user2)

    return new_room

def get_user_chatrooms(user):
    rooms = ChatRoom.objects.filter(
        people = user,
        is_active = True
    ).prefetch_related('people', ' messages').select_related('language')

    enriched_rooms = []
    for room in rooms:
        other_user = room.get_other_people(user)
        last_message = room.messages.last()
        unread_count = room.messages.filter(
            is_read=False
        ).exclude(sender=user).count()

        enriched_rooms.append({
            'room': room,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': unread_count,
            'last_activity': last_message.timestamp if last_message else room.created_at
        })

    enriched_rooms.sort(key=lambda x: x['last_activity'].timestamp, reverse=True)

    return enriched_rooms


def mark_message_as_read(chatroom, user):
    chatroom.messages.filter(
        is_read=False
    ).exclude(sender=user).update(is_read=True)
