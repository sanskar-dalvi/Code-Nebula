from fastapi import FastAPI
from api.routers import process_code

app = FastAPI()

# include the router
app.include_router(process_code.router)
