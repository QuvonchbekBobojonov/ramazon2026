from aiogram import types
from aiogram.filters import Command

from core.loader import dp


@dp.message(Command("getmyid"))
async def get_my_id_handler(message: types.Message) -> None:
    """
    Handler will reply with the user's Telegram ID when the /getmyid command is used
    """
    await message.answer(f"Your Telegram ID is: {message.from_user.id}")


@dp.message()
async def echo_handler(message: types.Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """
    try:
        # Send a copy of the received message
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer("Nice try!")
