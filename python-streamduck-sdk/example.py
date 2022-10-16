from client import Client, EventType

c = Client()
c.start()
print("started client")

@c.raw_event
async def event(res):
    print("new event")
    print(res)

# currently not working because of missing Json parser
@c.event(EventType.DeviceDisconnected)
async def device_disconnected(res):
    pass
