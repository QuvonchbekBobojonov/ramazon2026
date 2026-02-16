import logging
from aiogram import Bot

from core.config import ADMINS


from keyboards.inlines.admin_restart import restart_confirmation_keyboard

async def on_startup_notify(bot: Bot):
    """Notify admins about successful start and ask for restart broadcast confirmation"""
    for admin in ADMINS:
        try:
            await bot.send_message(
                chat_id=admin, 
                text="🚀 <b>Bot qayta ishga tushdi!</b>\n\nFoydalanuvchilarga bu haqda xabar yuborishni istaysizmi?",
                reply_markup=restart_confirmation_keyboard()
            )
        except Exception as err:
            logging.exception(err)


async def on_shutdown_notify(bot: Bot):
    """Notify admins about successful stop"""
    for admin in ADMINS:
        try:
            await bot.send_message(chat_id=admin, text="Bot to'xtadi.")
        except Exception as err:
            logging.exception(err)
