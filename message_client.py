import asyncio
import pickle
import uuid
import time

class MessageClient:
    def __init__(self, host="127.0.0.1", port=8888):
        self.host = host
        self.port = port

    def make_message(self, action, channel, message=None):
        """Формирование контейнера сообщения."""
        return {
            'action': action,
            'channel': channel,
            'time': self.cur_tm(),
            'message': message
        }

    def cur_tm(self):
        """Текущая метка времени."""
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    async def send_message(self, message):
        """Отправка сообщения на сервер."""
        reader, writer = await asyncio.open_connection(self.host, self.port)

        # Сериализуем сообщение
        serialized_message = pickle.dumps(message)
        writer.write(len(serialized_message).to_bytes(8, 'big'))
        writer.write(serialized_message)
        await writer.drain()

        # Получаем ответ от сервера
        raw_size = await reader.read(8)
        size = int.from_bytes(raw_size, 'big')
        response = await reader.read(size)
        response = pickle.loads(response)
        print(f"Ответ от сервера: {response}")

        writer.close()
        await writer.wait_closed()

    async def subscribe_channel(self, channel_name, callback):
        """Подписка на канал и обработка сообщений через callback."""
        reader, writer = await asyncio.open_connection(self.host, self.port)

        message = self.make_message("SUBSCRIBE", channel_name)
        serialized_message = pickle.dumps(message)
        writer.write(len(serialized_message).to_bytes(8, 'big'))
        writer.write(serialized_message)
        await writer.drain()

        while True:
            raw_size = await reader.read(8)
            if not raw_size:
                break
            size = int.from_bytes(raw_size, 'big')
            response = await reader.read(size)
            callback(pickle.loads(response))

        writer.close()
        await writer.wait_closed()

    def create_channel(self, channel="default"):
        """Создание канала на сервере."""
        message = self.make_message("CREATE_CHANNEL", channel)
        asyncio.run(self.send_message(message))

    def send(self, message, channel="default"):
        """Отправка сообщения в канал."""
        message_box = self.make_message("SEND", channel, message)
        asyncio.run(self.send_message(message_box))

    def subscribe(self, channel, callback):
        """Подписка на канал с использованием callback."""
        asyncio.run(self.subscribe_channel(channel, callback))

    def get_message(self, channel="default", message_id=None):
        """Получение сообщения по ID или последнего сообщения в канале."""
        message = self.make_message("GET_MESSAGE", channel, {"message_id": message_id})
        asyncio.run(self.send_message(message))

    def get_messages(self, channel="default"):
        """Получение всех сообщений в канале."""
        message = self.make_message("GET_MESSAGES", channel)
        asyncio.run(self.send_message(message))
    
    def clear_messages(self, channel="default"):
        """Очистка канала на сервере."""
        message = self.make_message("CLEAR_MESSAGES", channel)
        asyncio.run(self.send_message(message))

# Пример использования клиента
if __name__ == "__main__":
    client = MessageClient()

    # Создание канала
    # client.create_channel("test_channel")

    # for num in range(100):

    #     # Отправка сообщения
    #     client.send(f"тестовое сообщение! {num}", "test_channel")
    #     time.sleep(10)

    # # Подписка на канал и получение сообщений
    # def handle_message(response):
    #     print(f"Получено сообщение: {response}")

    # client.subscribe("test_channel", handle_message)

    # # Получение последнего сообщения
    # client.get_message("test_channel")

    #client.clear_messages("test_channel")
    
    # Получение всех сообщений в канале
    client.get_messages("test_channel")
    
    
