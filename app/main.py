from fastapi import FastAPI

from . import views


app = FastAPI(title='ITForDesigners')

@app.on_event('startup')
async def startup():
    ...

@app.on_event('shutdown')
async def shutdown():
    ...


app.include_router(views.auth_router, prefix='/api')
app.include_router(views.users_router, prefix='/api')
