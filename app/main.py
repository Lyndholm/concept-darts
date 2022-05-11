from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import views


app = FastAPI(title='ITForDesigners')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.on_event('startup')
async def startup():
    ...

@app.on_event('shutdown')
async def shutdown():
    ...


app.include_router(views.auth_router, prefix='/api')
app.include_router(views.users_router, prefix='/api')
app.include_router(views.worlds_router, prefix='/api')
