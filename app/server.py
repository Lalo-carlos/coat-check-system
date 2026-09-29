import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.production import app as production_app
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

production_app.mount("/static", StaticFiles(directory="static"), name="static")

@production_app.get("/")
def root():
    return FileResponse("static/index.html")

app = production_app
