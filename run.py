import asyncio

from parser import Parser

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(Parser.run())
    loop.run_forever()
