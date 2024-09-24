import asyncio
import json
import pickle
import threading
import uuid
import time
import os
from multiprocessing import shared_memory, Lock

class MessageServer:
    def __init__(self, host="127.0.0.1", port=8888):
        self.host = host
        self.port = port
        self.channels = {}  # Для хранения каналов и подписчиков
        self.is_running = True
        self.shared_mem = None
        self.lock = Lock()  # Мьютекс для синхронизации доступа к разделяемой памяти
        self.use_shared_memory = False
        self.shared_memory_name = 'message_shared_mem'
        self.local_clients = []  # Хранение локальных клиентов

    # --- Работа с каналами ---
    def create_channel(self, channel_name):
        if channel_name not in self.channels:
            self.channels[channel_name] = {"subscribers": [], "messages": []}
            print(f"Канал {channel_name} создан.")

    def subscribe_to_channel(self, channel_name, writer):
        if channel_name in self.channels:
            if writer not in self.channels[channel_name]["subscribers"]:
                self.channels[channel_name]["subscribers"].append(writer)
                print(f"Подписка на канал {channel_name} успешна.")

    async def send_message_to_channel(self, channel_name, message, is_local):
        if channel_name in self.channels:
            self.channels[channel_name]["messages"].append(message)

            # Отправляем сообщение всем подписчикам
            for subscriber in self.channels[channel_name]["subscribers"]:
                try:
                    # Проверяем, локальный ли это клиент
                    if is_local:
                        subscriber.write(json.dumps({"message_location": "shared_memory"}).encode())
                    else:
                        subscriber.write(json.dumps(message).encode())
                    await subscriber.drain()
                except Exception as e:
                    print(f"Ошибка при отправке сообщения подписчику: {e}")

    # --- Работа с разделяемой памятью ---
    def enable_shared_memory(self, size=1024):
        """Включение разделяемой памяти"""
        try:
            self.shared_mem = shared_memory.SharedMemory(name=self.shared_memory_name, create=True, size=size)
            self.use_shared_memory = True
            print("Разделяемая память включена.")
        except Exception as e:
            print(f"Ошибка при создании разделяемой памяти: {e}")

    def disable_shared_memory(self):
        """Отключение разделяемой памяти"""
        try:
            if self.shared_mem:
                self.shared_mem.close()
                self.shared_mem.unlink()
            self.use_shared_memory = False
            print("Разделяемая память отключена.")
        except Exception as e:
            print(f"Ошибка при отключении разделяемой памяти: {e}")

    def write_to_shared_memory(self, data):
        """Запись данных в разделяемую память"""
        with self.lock:
            data_bytes = pickle.dumps(data)  # Сериализация объекта через pickle
            self.shared_mem.buf[:len(data_bytes)] = data_bytes
            print(f"Данные записаны в разделяемую память: {data}")

    def read_from_shared_memory(self):
        """Чтение данных из разделяемой памяти"""
        with self.lock:
            data = pickle.loads(self.shared_mem.buf.tobytes().rstrip(b'\x00'))  # Десериализация объекта
            return data

    # --- Формирование сообщения (контейнер) ---
    def make_message(self, action, channel, message, message_type):
        mess_box = {
            'action': action,
            'channel': channel,
            'message_type': message_type,
            'message_id': str(uuid.uuid4()),  # Уникальный идентификатор сообщения
            'time': self.cur_tm(),
            'message': message
        }
        return mess_box

    def cur_tm(self):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    # --- Обработка клиента ---
    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        is_local = self.is_local_connection(addr[0])
        print(f"Клиент {addr} подключен. Локальный: {is_local}")
        
        try:
            while self.is_running:
                data = await reader.read(1024)
                if not data:
                    break

                if is_local:  # Локальный клиент
                    message = pickle.loads(data)
                else:  # Удаленный клиент
                    message = json.loads(data.decode())

                action = message.get("action")

                if action == "CREATE_CHANNEL":
                    channel_name = message.get("channel")
                    self.create_channel(channel_name)
                    response = self.make_message("response", channel_name, f"Канал {channel_name} создан.", "text")
                    writer.write(json.dumps(response).encode())
                    await writer.drain()

                elif action == "SUBSCRIBE":
                    channel_name = message.get("channel")
                    self.subscribe_to_channel(channel_name, writer)
                    response = self.make_message("response", channel_name, f"Подписка на {channel_name} успешна.", "text")
                    writer.write(json.dumps(response).encode())
                    await writer.drain()

                elif action == "SEND":
                    channel_name = message.get("channel")
                    message_content = message.get("message")
                    message_type = message.get("message_type", "text")

                    if is_local:
                        self.write_to_shared_memory(message_content)
                        await self.send_message_to_channel(channel_name, self.make_message("notification", channel_name, "stored in shared memory", message_type), is_local=True)
                    else:
                        await self.send_message_to_channel(channel_name, self.make_message("notification", channel_name, message_content, message_type), is_local=False)
                    
                    response = self.make_message("response", channel_name, f"Сообщение отправлено в {channel_name}.", "text")
                    writer.write(json.dumps(response).encode())
                    await writer.drain()

                elif action == "READ_SHARED_MEMORY":
                    shared_data = self.read_from_shared_memory()
                    response = self.make_message("response", "shared_memory", shared_data, "class")
                    writer.write(json.dumps(response).encode())
                    await writer.drain()

                elif action == "ENABLE_SHARED_MEMORY":
                    self.enable_shared_memory()
                    response = self.make_message("response", "shared_memory", "Разделяемая память включена.", "text")
                    writer.write(json.dumps(response).encode())
                    await writer.drain()

                elif action == "STOP":
                    await self.shutdown()
                    response = self.make_message("response", "server", "Сервер остановлен.", "text")
                    writer.write(json.dumps(response).encode())
                    await writer.drain()

                else:
                    response = self.make_message("response", "unknown", "Неизвестная команда.", "text")
                    writer.write(json.dumps(response).encode())
                    await writer.drain()

        except Exception as e:
            print(f"Ошибка при обработке клиента: {e}")
        finally:
            print(f"Клиент {addr} отключен.")
            writer.close()
            await writer.wait_closed()

    # --- Остановка сервера ---
    async def shutdown(self):
        self.is_running = False
        if self.use_shared_memory:
            self.disable_shared_memory()
        print("Сервер остановлен.")

    # --- Определение локальности подключения ---
    def is_local_connection(self, client_ip):
        """Проверка, является ли клиент локальным (тот же компьютер)"""
        return client_ip == "127.0.0.1" or client_ip == os.getenv('HOST_IP', '127.0.0.1')

    # --- Запуск сервера ---
    async def start(self):
        try:
            server = await asyncio.start_server(self.handle_client, self.host, self.port)
            async with server:
                print(f"Сервер запущен на {self.host}:{self.port}")
                await server.serve_forever()
        except Exception as e:
            print(f"Ошибка при запуске сервера: {e}")

def start_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    server = MessageServer()
    loop.run_until_complete(server.start())

if __name__ == "__main__":
    try:
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        print("Сервер запущен, ожидаем подключения клиентов...")
        server_thread.join()
    except Exception as e:
        print(f"Ошибка при запуске сервера: {e}")
