from sqladmin import Admin, ModelView
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from db.models import User

class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.telegram_id, User.full_name, User.username, User.region, User.created_at]
    column_searchable_list = [User.full_name, User.username, User.telegram_id]
    column_filters = [User.region, User.created_at]
    name = "Foydalanuvchi"
    name_plural = "Foydalanuvchilar"
    icon = "fa-solid fa-user"

def setup_admin(app: FastAPI, engine: AsyncEngine):
    admin = Admin(app, engine, title="Ramazon 2026 Admin")
    admin.add_view(UserAdmin)
