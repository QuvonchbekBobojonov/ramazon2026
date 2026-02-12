from aiogram import Dispatcher
from .user_registration import UserRegistrationMiddleware

def setup_middlewares(dp: Dispatcher):
    dp.message.outer_middleware(UserRegistrationMiddleware())
    dp.callback_query.outer_middleware(UserRegistrationMiddleware())

