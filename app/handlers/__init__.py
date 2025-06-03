from app.handlers.common import router as common_router
from app.handlers.business_lunch import router as business_lunch_router
from app.handlers.menu_search import router as menu_search_router
from app.handlers.hookah import router as hookah_router
from app.handlers.reviews import router as reviews_router
from app.handlers.admin import router as admin_router

routers = [
    menu_search_router,
    business_lunch_router,
    hookah_router,
    reviews_router,
    admin_router,
    common_router
]

__all__ = ['routers'] 