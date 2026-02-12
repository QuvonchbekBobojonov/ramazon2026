from aiogram import Dispatcher
from .user_registration import UserRegistrationMiddleware

def setup_middlewares(dp: Dispatcher):
    dp.update.outer_middleware(UserRegistrationMiddleware())
