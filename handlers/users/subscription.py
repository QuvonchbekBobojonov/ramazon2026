from aiogram import types
from aiogram.fsm.context import FSMContext
from core.loader import dp, bot
from utils.subscription import check_membership, get_subscription_keyboard, SUBSCRIPTION_TEXT
from keyboards.default.ramadan_menu import get_ramadan_menu
from handlers.users.start import command_start_handler
from utils.cache import redis_client
import logging

@dp.callback_query(lambda c: c.data == "check_subs")
async def check_subs_callback(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.answer("🔄 Obunalar tekshirilmoqda...", show_alert=False)
    except Exception:
        pass
    
    user_id = call.from_user.id
    is_subscribed = await check_membership(user_id)
    
    if is_subscribed:
        # Update cache so middleware doesn't block again
        if redis_client:
            try:
                cache_key = f"user_sub:{user_id}"
                redis_client.set(cache_key, "1", ex=600)
            except Exception as e:
                logging.error(f"Error updating sub cache: {e}")

        try:
            await call.message.delete()
        except:
            pass
        await call.message.answer("✅ Obuna tasdiqlandi! Botdan foydalanishingiz mumkin.")
        await command_start_handler(call.message, state, user=call.from_user)
    else:
        # Update cache as not subscribed just in case
        if redis_client:
            try:
                cache_key = f"user_sub:{user_id}"
                redis_client.set(cache_key, "0", ex=600)
            except Exception:
                pass
        try:
            await call.message.edit_text(SUBSCRIPTION_TEXT, reply_markup=get_subscription_keyboard())
        except:
             await call.message.answer(SUBSCRIPTION_TEXT, reply_markup=get_subscription_keyboard())
