from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from fastapi import FastAPI, Request
from sqlalchemy.ext.asyncio import AsyncEngine
import os

from db.models import User

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form.get("username"), form.get("password")
        
        admin_user = os.getenv("ADMIN_USERNAME", "admin")
        admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")

        if username == admin_user and password == admin_pass:
            request.session.update({"token": "authenticated"})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("token") == "authenticated"

authentication_backend = AdminAuth(secret_key=os.getenv("BOT_TOKEN", "secret"))

from markupsafe import Markup

class UserAdmin(ModelView, model=User):
    column_list = ["id", "telegram_id", "full_name", "username", "region", "profile_link", "created_at"]
    # Removed filters and search due to sqladmin compatibility issues




    
    column_formatters = {
        "profile_link": lambda m, a: Markup(
            f'<a href="https://t.me/{m.username}" target="_blank">@{m.username}</a>' if m.username 
            else f'<a href="tg://user?id={m.telegram_id}">User Profile</a>'
        )
    }
    
    name = "Foydalanuvchi"
    name_plural = "Foydalanuvchilar"
    icon = "fa-solid fa-user"




def setup_admin(app: FastAPI, engine: AsyncEngine):
    admin = Admin(app, engine, title="Ramazon 2026 Admin", authentication_backend=authentication_backend)
    admin.add_view(UserAdmin)

