import socket
import sys
import threading
import json
import asyncio
from functools import wraps
from enum import Enum

class EventType(Enum):
    DeviceDisconnected = 1,
    DeviceConnected = 2

class UnknownEventType(Exception):
    def __init__(self):
        pass
    def __str__(self):
        return repr(f"The argument has to be a valid EventType ({EventType}).")

class EventTypeHandlerExists(Exception):
    def __init__(self, etype: EventType):
        self.etype = etype
    def __str__(self):
        return repr(f"An EventType handler already exists for {self.etype.name}. Please use another EventType or delete the other one.")

"""
The client for the Streamduck socket
"""
class Client:
    def __init__(self, custom_platform=None):
        if custom_platform in ["linux", "darwin", "win32"]:
            self.platform = custom_platform
        if sys.platform in ["linux", "darwin"]:
            self.platform = "unix"
        elif sys.platform == "win32":
            self.platform = "windows"
        else:
            print(f"Platform \"{sys.platform}\" is not supported")

        self.client = None,

        self.raw_event_callbacks = []
        self.event_callbacks = {}

        # self.queue_thread = threading.Thread(target=self._create_queue_manager)
        # self.queue_thread.start()

    """
    Convenience function to start the receiver in a thread
    """
    def start(self):
        self.async_loop = asyncio.get_event_loop()
        self.receiver_task = asyncio.run_coroutine_threadsafe(self._create_receiver(), self.async_loop)
        self.receiver_thread = threading.Thread(target=self.async_loop.run_forever)
        self.receiver_thread.start()

    """
    Converts the decoded text from the receiver to json and sends it to the corresponding function which were declared by the decorators
    """
    async def _manage_callback(self, event):
        #print(event)
        print(self.raw_event_callbacks)
        print(self.event_callbacks)
        try:
            pass
            # TODO: fix JSON
            # jason = [json.loads(line) for line in event]
            # jason = json.loads(event);
            # print(jason)
        except ValueError as e:
            print(f"Unable to retrieve Json. Is your SDK and daemon up to date? Error: \"{e}\"")

        print(self.raw_event_callbacks)
        for function in self.raw_event_callbacks:
            await function(event)
        if len(self.event_callbacks) == 0:
            return
        # for function in self.event_callback:
        #   await function(json)

    """
    Create a socket receiver to listen to the daemon. Calls self._manage_callback to process the data
    """
    async def _create_receiver(self):
        if self.platform == "unix":
            socket_type = socket.AF_UNIX
            sock_file = "/tmp/streamduck.sock"

        with socket.socket(socket_type, socket.SOCK_STREAM) as s:
            s.connect(sock_file)
            while True:
                await self._manage_callback(s.recv(1024).decode())

    """Decorator for all type of events. Outputs unparsed Json."""
    def raw_event(self, coro):
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError("You have to use a coroutine function for an event.")

        self.raw_event_callbacks.append(coro)
        return coro

    """
    A decorator for an event coming from the server.

    Example
    ----

    @client.event(EventType.DeviceConnected)
    def on_device_connected(mes):
        print(mes)
    """
    def event(self, etype: EventType):
        def decorate(coro):
            if not isinstance(etype, EventType):
                raise UnknownEventType
            if etype in self.event_callbacks.keys():
                raise EventTypeHandlerExists(etype)
            if not asyncio.iscoroutinefunction(coro):
                raise TypeError("You have to use a coroutine function for an event.")
            self.event_callbacks[etype] = coro
        return decorate

