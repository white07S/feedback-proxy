import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import db
from feedback_router import router

app = FastAPI(title="Light Feedback API", version="0.1.0")

# CORS for CRA dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the feedback router
app.include_router(router)


@app.on_event("startup")
async def startup():
    # Run blocking DB initialization in a worker thread so that
    # asyncpg can manage its own event loop without clashing with
    # FastAPI/uvicorn's main event loop.
    await asyncio.to_thread(db.init_db)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
