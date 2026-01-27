from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
# Language selection
class Language(models.Model):
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=5)

    def __str__(self):
        return self.name

# Users, pro_level = proficiency level  native_lang = native_language, Learn_lang = Learning_language

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    email = models.EmailField()
    native_lang = models.ForeignKey(Language,
                                    on_delete=models.SET_NULL,
                                    null=True,
                                    related_name='native_speakers')
    learn_lang = models.ManyToManyField(Language, related_name='learners')
    PROFICIENCY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('native', 'Native'),
    ]
    pro_level = models.CharField(max_length=25,
                                 choices=PROFICIENCY_CHOICES,
                                 default='beginner')
    bio = models.TextField(blank=True)
    def __str__(self):
        return self.user.username


# Should auto create profile when user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

# Chat Room two users practicing a language lang = Language,

class ChatRoom(models.Model):
    name = models.CharField(max_length=75)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    people = models.ManyToManyField(User, related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def find_other_people(self, user):
        return self.people.exclude(id=user.id).first()

    class Meta:
        ordering = ['-updated_at']


# Individual messages in a chat room
class Message(models.Model):
    chatroom = models.ForeignKey(ChatRoom,
                                  on_delete=models.CASCADE,
                                  related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    def content_preview(self):
        return self.content[:50]
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"

    class Meta:
        ordering = ['-timestamp']