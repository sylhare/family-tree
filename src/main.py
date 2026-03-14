from fastapi import FastAPI

from .routes import router as genealogy_router

app = FastAPI(title="Genealogical Tree API", version="0.2.0")

# Wire routers
app.include_router(genealogy_router) 