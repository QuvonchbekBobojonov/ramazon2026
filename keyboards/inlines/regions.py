from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.ramadan_data import ramadan_data

def get_regions_keyboard():
    builder = InlineKeyboardBuilder()
    regions = ramadan_data["regional_offsets"].keys()
    
    for region in regions:
        if region in ["unit", "description"]:
            continue
        display_name = region.replace("_", " ").title()
        builder.button(text=display_name, callback_data=f"region:{region}")
    
    builder.adjust(2)
    return builder.as_markup()
