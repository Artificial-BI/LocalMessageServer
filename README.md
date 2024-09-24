
# Message Exchange System

This project implements an asynchronous, multi-threaded message exchange system, designed for real-time communication between clients over TCP sockets. The system is built with Python using the `asyncio` library for asynchronous operations, and `pickle` for full message serialization, which enables handling a wide range of data types including large messages.

## Features

1. **Asynchronous Operations**: All communication operations (sending, receiving, subscribing) are asynchronous, allowing multiple clients to interact with the server without blocking.
2. **Multi-threading**: The server runs in a separate thread, enabling it to accept and process messages from different applications running simultaneously.
3. **Command-based Server Management**: The server can be started and stopped via commands, making it easy to manage.
4. **Two Modes of Operation**:
   - **Read/Write Mode**: Clients can send and retrieve messages from channels.
   - **Subscription Mode**: Clients can subscribe to specific channels to receive real-time updates whenever a new message is posted.
5. **Support for Multiple Data Types**: Messages can contain a variety of data types including `text`, `bool`, `int`, `float`, `dict`, `class`, and more. All data is serialized using `pickle`.
6. **Socket-based Communication**: All communication between clients and the server happens through TCP sockets, allowing seamless network-based messaging.
7. **Dynamic Message Buffer**: The system automatically adjusts the buffer size based on the size of the message, making it capable of handling messages of any size—from a few bytes to several gigabytes.
8. **Cross-platform**: The system works on both Windows and Linux platforms and is designed to be easily portable.
9. **Message Containers**: All messages are encapsulated in a standard container with the following structure:
   ```python
   mess_box = {
       'action': action,
       'channel': channel,
       'message_id': uuid.uuid4(),
       'time': self.cur_tm(),
       'message': message
   }
   ```

## Message Flow

1. **Client-side Preparation**: The client forms a message by creating a message container:
   ```python
   mess_box = pickle.dumps({
       'action': action,
       'channel': channel,
       'time': self.cur_tm(),
       'message': message
   })
   ```
   The message is serialized with `pickle` and sent to the server.
   
2. **Server-side Handling**: 
   - The server receives the serialized message, assigns it a unique `message_id`, and stores it in a list of messages for the respective channel.
   - If the number of stored messages exceeds 1000, the oldest messages are deleted.
   - The server then sends the `message_id` back to the client.

3. **Client Requests**:
   - The client can request a specific message by its `message_id` or retrieve the latest message from a channel using the `GET_MESSAGE` action.
   - The client can also request the entire list of messages from a channel with the `GET_MESSAGES` action.

4. **Real-time Message Broadcast**:
   - When a new message is sent to a channel, all clients subscribed to that channel immediately receive the message.
   - The server manages the subscriptions and broadcasts messages accordingly.

## Installation

To use this system, follow these steps:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Artificial-BI/MessageServer.git
   cd message-exchange-system
   ```

2. **Create a virtual environment and activate it**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/Mac
   .venv\Scripts\activate    # Windows
   ```

3. **Install required dependencies**:
   The system only requires Python's standard libraries (`asyncio`, `pickle`, `uuid`, `time`), so no additional packages need to be installed.

## Usage

### Starting the Server

To start the server, simply run the following command:
```bash
python server.py
```

The server will start in a separate thread and will listen for incoming client connections on `localhost:8888`. The server handles multiple clients concurrently and supports both sending and receiving messages in real-time.

### Client Operations

1. **Creating a Channel**:
   The client can create a channel by sending a message to the server with the `CREATE_CHANNEL` action. For example:
   ```python
   client.create_channel("test_channel")
   ```

2. **Sending a Message**:
   To send a message to a specific channel, use the `SEND` action:
   ```python
   client.send("Hello, this is a test message!", "test_channel")
   ```

3. **Subscribing to a Channel**:
   The client can subscribe to a channel and receive all new messages posted to that channel in real-time:
   ```python
   def handle_message(response):
       print(f"Received message: {response}")

   client.subscribe("test_channel", handle_message)
   ```

4. **Retrieving Specific Messages**:
   - **Get Latest Message**: To get the latest message from a channel:
     ```python
     client.get_message("test_channel")
     ```
   - **Get Message by ID**: To get a specific message by its ID:
     ```python
     client.get_message("test_channel", message_id="some-uuid-id")
     ```

5. **Retrieving All Messages**:
   The client can request all messages from a specific channel using the `GET_MESSAGES` action:
   ```python
   client.get_messages("test_channel")
   ```

6. **Stopping the Server**:
   To stop the server, send the `STOP` command:
   ```python
   client.send_stop_signal()
   ```

## Message Container Structure

Each message sent through the system follows the structure below:
```python
{
    'action': 'SEND',        # The action being performed (e.g., SEND, CREATE_CHANNEL, SUBSCRIBE, etc.)
    'channel': 'test_channel',  # The channel to which the message belongs
    'message_id': 'uuid',    # Unique identifier for the message
    'time': '2024-09-19 12:00:00', # Timestamp of when the message was created
    'message': <message>     # The actual content of the message (serialized via pickle)
}
```

## Supported Actions

- **CREATE_CHANNEL**: Create a new channel.
- **SEND**: Send a message to a specific channel.
- **SUBSCRIBE**: Subscribe to a channel to receive real-time updates.
- **UNSUBSCRIBE**: Unsubscribe from a channel.
- **GET_MESSAGE**: Retrieve a specific message by ID or the latest message if no ID is provided.
- **GET_MESSAGES**: Retrieve all messages from a specific channel.
- **STOP**: Stop the server.

## Future Improvements

- **Authentication**: Implement user authentication to allow only authorized users to send or receive messages.
- **Persistent Storage**: Add a database to store messages permanently.
- **WebSocket Support**: Add WebSocket support for better real-time communication over the web.
- **Encryption**: Add encryption for secure communication between the client and server.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

This system provides a robust, flexible platform for real-time messaging, supporting a wide range of data types and asynchronous communication across multiple clients and channels. It can be easily expanded and integrated into larger systems for a variety of use cases, including chat applications, distributed systems, and real-time data streaming.
