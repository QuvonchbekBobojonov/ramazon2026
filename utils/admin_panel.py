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

class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.telegram_id, User.full_name, User.username, User.region, User.created_at]
    column_searchable_list = [User.full_name, User.username, User.telegram_id]
    column_filters = [User.region, User.created_at]
    name = "Foydalanuvchi"
    name_plural = "Foydalanuvchilar"
    icon = "fa-solid fa-user"

def setup_admin(app: FastAPI, engine: AsyncEngine):
    admin = Admin(app, engine, title="Ramazon 2026 Admin", authentication_backend=authentication_backend)
    admin.add_view(UserAdmin)

