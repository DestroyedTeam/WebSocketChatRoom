from fastapi import APIRouter
from .page import router as page_router

router = APIRouter()
router.include_router(page_router)
