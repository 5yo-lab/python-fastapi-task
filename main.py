from fastapi import FastAPI

app = FastApi()

@app.get("/")
def index():
    return {"Hello world!"}