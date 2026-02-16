from aiogram import Dispatcher
from .user_registration import UserRegistrationMiddleware
from .subscription import SubscriptionMiddleware

def setup_middlewares(dp: Dispatcher):
    dp.message.outer_middleware(UserRegistrationMiddleware())
    dp.callback_query.outer_middleware(UserRegistrationMiddleware())
    
    # Obunani tekshirish middleware
    dp.message.outer_middleware(SubscriptionMiddleware())
    dp.callback_query.outer_middleware(SubscriptionMiddleware())

