from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import subprocess

app = FastAPI()

@app.on_event("startup")
async def start_streamlit():
    subprocess.Popen([
        "streamlit", "run", "streamlit_app.py",
        "--server.address", "0.0.0.0",  # 이 부분 추가
        "--server.port", "8501"         # 포트 명시 (기본 8501)
    ])

@app.get("/")
async def root():
    # 여기서 "localhost" 대신 외부 접속용 주소로 리디렉션
    return RedirectResponse(url="http://test.dths.my:8501")  # ★
