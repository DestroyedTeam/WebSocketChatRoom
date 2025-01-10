from fastapi import APIRouter
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/chat")
async def get_page(request: Request):
    return templates.TemplateResponse("simple_chatroom.html", {"request": request})
