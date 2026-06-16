"""
Exposes internal endpoints strictly for debugging email templates during development.
Allows developers to render Jinja2 HTML templates in the browser without actually sending an email.
"""
import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

from src.shared.config import app_settings, email_settings, url_settings

router = APIRouter(prefix="/dev")

def dev_enabled():
    if app_settings.ENV != "development":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dev routes disabled")
    return True


@router.get("/email/preview/{template_path:path}", response_class=HTMLResponse, dependencies=[Depends(dev_enabled)])
async def preview_email(request: Request, template_path: str = "", theme: str | None = None):
    """
    If no template_path is provided, renders the Gallery View of all templates.
    If template_path is provided, renders the specific template.
    """
    tmpl_root = Path(__file__).parents[2] / "templates" / "emails"
    
    # --- GALLERY VIEW ---
    env = Environment(loader=FileSystemLoader(tmpl_root))
    if not template_path:
        templates = []
        for f in tmpl_root.rglob("*.html"):
            if "layouts" not in f.parts and f.name != "dev_gallery.html":
                rel_path = f.relative_to(tmpl_root).as_posix()
                templates.append(rel_path)
                
        themes = ["modern", "minimal", "playful"]
        active_theme = theme if theme else email_settings.TEMPLATE_NAME
        
        gallery_tmpl = env.get_template("dev_gallery.html")
        html = gallery_tmpl.render(themes=themes, active_theme=active_theme, templates=templates)
        return HTMLResponse(content=html)

    # --- INDIVIDUAL TEMPLATE VIEW ---
    env = Environment(loader=FileSystemLoader(tmpl_root))
    env.globals["now"] = datetime.datetime.now
    try:
        jinja_tmpl = env.get_template(template_path)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Template not found: {exc}")

    active_theme = theme if theme else email_settings.TEMPLATE_NAME
    dummy_context = {
        "proj_name": "FastAPI OAuth",
        "name": "Demo User",
        "login_url": f"{url_settings.FRONTEND_URL}/",
        "reset_url": f"{url_settings.FRONTEND_URL}/reset-password?token=abc123",
        "otp": "123456",
        "theme": active_theme,
    }
    rendered = jinja_tmpl.render(**dummy_context)
    return HTMLResponse(content=rendered)
