# main.py
import asyncio
from aiogram import Bot, Dispatcher
from handlers import dp
from config import TOKEN
from handlers import register
from handlers import register
async def main() -> None:
    bot = Bot(TOKEN)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    dp.startup.register(register.menu) # установка стартового состояния. Убрать при необходимости