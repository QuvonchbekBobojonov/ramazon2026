from aiogram import types
from aiogram.fsm.context import FSMContext
from core.loader import dp, bot
from utils.subscription import check_membership, get_subscription_keyboard, SUBSCRIPTION_TEXT
from keyboards.default.ramadan_menu import get_ramadan_menu
from handlers.users.start import command_start_handler

@dp.callback_query(lambda c: c.data == "check_subs")
async def check_subs_callback(call: types.CallbackQuery, state: FSMContext):
    await call.answer("🔄 Obunalar tekshirilmoqda...", show_alert=False)
    
    user_id = call.from_user.id
    is_subscribed = await check_membership(user_id)
    
    if is_subscribed:
        try:
            await call.message.delete()
        except:
            pass
        await call.message.answer("✅ Obuna tasdiqlandi! Botdan foydalanishingiz mumkin.", reply_markup=get_ramadan_menu())
        # Re-trigger start logic to show menu/register
        # We need to create a dummy message to pass to the handler
        # Or just call the logic directly. Calling logic directly is safer.
        await command_start_handler(call.message, state)
    else:
        try:
            await call.message.edit_text(SUBSCRIPTION_TEXT, reply_markup=get_subscription_keyboard())
        except:
             await call.message.answer(SUBSCRIPTION_TEXT, reply_markup=get_subscription_keyboard())
