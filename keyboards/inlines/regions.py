from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.ramadan_data import ramadan_data

def get_regions_keyboard():
    builder = InlineKeyboardBuilder()
    viloyatlar = ramadan_data["viloyatlar"].keys()
    
    for viloyat in viloyatlar:
        builder.button(text=viloyat, callback_data=f"viloyat:{viloyat}")
    
    builder.adjust(2)
    return builder.as_markup()

def get_districts_keyboard(viloyat: str):
    builder = InlineKeyboardBuilder()
    districts = ramadan_data["viloyatlar"].get(viloyat, [])
    
    for district in districts:
        # Standardize slug: lowercase, remove special chars
        slug = district.lower().replace("'", "").replace(" ", "").replace("o'", "o").replace("g'", "g").replace("'", "")
        # Further manual check to match ramadan_data keys
        if "qashqadaryo" in viloyat.lower() and district == "Qarshi": slug = "qarshi"
        if "xorazm" in viloyat.lower() and district == "Urgench": slug = "urganch"
        if "samarqand" in viloyat.lower() and district == "Samarqand": slug = "samarqand"
        if "navoiy" in viloyat.lower() and district == "Navoiy": slug = "navoiy"
        if "buxoro" in viloyat.lower() and district == "Buxoro": slug = "buxoro"
        if "fargona" in viloyat.lower() and district == "Fargona": slug = "fargona"
        if "namangan" in viloyat.lower() and district == "Namangan": slug = "namangan"
        if "andijon" in viloyat.lower() and district == "Andijon": slug = "andijon"
        if "sirdaryo" in viloyat.lower() and district == "Guliston": slug = "guliston"
        if "jizzax" in viloyat.lower() and district == "Jizzax": slug = "jizzax"
        if "surxondaryo" in viloyat.lower() and district == "Termiz": slug = "termiz"
        
        builder.button(text=district, callback_data=f"region:{slug}")
    
    builder.button(text="⬅️ Ortga", callback_data="back_to_regions")
    builder.adjust(2)
    return builder.as_markup()
