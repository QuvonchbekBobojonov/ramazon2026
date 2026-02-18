from sqladmin import Admin, ModelView
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine
from markupsafe import Markup

from db.models import User

class UserAdmin(ModelView, model=User):
    column_list = ["id", "telegram_id", "full_name", "username", "region", "is_subscribed", "is_blocked", "profile_link", "created_at"]
    
    column_formatters = {
        "profile_link": lambda m, a: Markup(
            f'<a href="https://t.me/{m.username}" target="_blank">@{m.username}</a>' if m.username 
            else f'<a href="tg://user?id={m.telegram_id}" class="btn btn-sm btn-outline-primary">Profile</a>'
        )
    }
    
    name = "Foydalanuvchi"
    name_plural = "Foydalanuvchilar"
    icon = "fa-solid fa-user"
    
    # Simple mobile-friendly adjustments via CSS can be injected if we override templates
    # For now, sqladmin uses Bootstrap which is responsive.

def setup_admin(app: FastAPI, engine: AsyncEngine):
    # Removing authentication_backend to disable login screen
    admin = Admin(app, engine, title="Ramazon 2026 Admin")
    admin.add_view(UserAdmin)
