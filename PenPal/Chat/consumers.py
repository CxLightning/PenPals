import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import ChatRoom, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self): #Called when connection is established

        self.room_id = self.scope['url_route']['kwargs']['room_id'] # get room id from url from Routing.py

        self.room_group_name = f' chat_{self.room_id}' # will create froup name for chat room and all users join same group

        self.user = self.scope['user'] # get user from scope from AuthMiddlewareStack

        if not self.user.is_authenticated: # will reject if user not logged in.
            await self.accept()
            return

        is_participant = await self.check_room_participant()
        if not is_participant:

            await self.close()
            return


        await self.channels_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        await self.channel_layer.group_send(
            self.room_group_name,
        {
                'type': 'user_joined',
            'username': self.user.username,
        })

    async def disconnect(self, close_code):

        await self.channel_layer.group_send(
            self.room_group_name,{
                'type': 'user_left',
                'username': self.user.username,
            })


        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):

        try:
            data = json.loads(text_data)
        except json.decoder.JSONDecodeError:
            return

        message_type = data.get('type', 'chat_message')

        if message_type == 'chat_message':
            await self.handle_chat_message(data)

        elif message_type == 'typing':
            await self.handle_typing(data)

        elif message_type == 'read receipt':
            await self.handel_read_receipt(data)



    async def handle_chat_message(self,data):
        message_content = data.get('message', '').strip()

        if not message_content or len(message_content) > 2500:
            return

        message = await self.save_message(message_content)

        if message is None:
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'username': self.user.username,
                'message': message_content,
                'timestamp': message.timestamp,
                'message_id': message.id,
            }
        )

        async def handle_typing(self, data):

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'username': self.user.username,
                    'is_typing': data.get('is_typing', True),

                }
            )



        async def handle_read_receipt(self, data):
            message_ids = data.get('message_ids', [])

            await self.mark_messages_in_read(message_ids)



        async def chat_message(self, event):
            await self.send(text_data=json.dumps({
                'type': 'chat_message',
                'username': event['username'],
                'message': event['message'],
                'timestamp': event['timestamp'],
                'message_id': event['message_id'],
            }))


        async def typing_indicator(self, event):

            if event['username'] != self.user.username:
                await self.send(text_data=json.dumps({
                    'type': 'typing',
                    'username' : event['username'],
                    'is_typing' : event.get ('is_typing', True)
                }))


        async def user_join(self, event):
            await self.send(text_data=json.dumps({
                'type': 'user_join',
                'username' : event['username'],
            }))

        async def user_leave(self, event):
            if event['username'] != self.user.username: await self.send(text_data=json.dumps({
                'type': 'user_leave',
                'username' : event['username'],
            }))



# Database Operations

def check_room_participant(self):

    try:
        room = ChatRoom.objects.get(id=self.room_id)
        return room.people.filter(user=self.user.id).exists()
    except ChatRoom.DoesNotExist:
        return False


def save_message(self, content):

    try:
        room = ChatRoom.objects.get(id=self.room_id)
        message = Message.objects.create(
            chatroom=room,
            sender=self.user,
            content=content,
        )
        return message
    except ChatRoom.DoesNotExist:
        return None
    except Exception as e:
        print(f'Error saving message: {e}')
        return None



@database_sync_to_async
def mark_messages_in_read(self, message_ids):

    try:
        Message.objects.filter(id__in=message_ids, chatroom_id=self.room_id).exclude(sender=self.user).update(is_read=True)
    except Exception as e:
        print(f'Error making messages as read: {e}')


