import os
from pathlib import Path
from fastapi import FastAPI
from dotenv import load_dotenv
from prompty.tracer import trace
from prompty.core import PromptyStream
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from tracing import init_tracing
from orchestrator import Task, create

base = Path(__file__).resolve().parent


load_dotenv()
LOCAL_TRACING = True if os.getenv("LOCAL_TRACING", "false").lower() == "true" else False
tracer = init_tracing()


app = FastAPI()

code_space = os.getenv("CODESPACE_NAME")

if code_space: 
    origin_8000= f"https://{code_space}-8000.app.github.dev"
    origin_5173 = f"https://{code_space}-5173.app.github.dev"
    origins = [origin_8000, origin_5173]
else:
    origins = [
        o.strip()
        for o in Path(Path(__file__).parent / "origins.txt").read_text().splitlines()
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/api/article")
@trace
async def create_article(task: Task):
    return StreamingResponse(
        PromptyStream(
            "create_article", create(task.research, task.products, task.assignment)
        ),
        media_type="application/x-ndjson",
    )


FastAPIInstrumentor.instrument_app(app)
