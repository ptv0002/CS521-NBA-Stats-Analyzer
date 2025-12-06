# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from backend.model import list_players, get_player_averages
# from fastapi.templating import Jinja2Templates
# from fastapi.responses import HTMLResponse
# app = FastAPI()
#
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
#
# templates = Jinja2Templates(directory="../frontend/templates")
# @app.get("/")
# def home():
#     return {"status": "NBA backend running"}
#
# @app.get("/players")
# def get_players():
#     return list_players()
#
# @app.get("/player_averages")
# def player_averages():
#     df = get_player_averages(
#         "backend/data/players.csv",
#         "backend/data/PlayerStatistics.csv"
#     )
#     return df.to_dict(orient="records")
#
# @app.get("/", response_class=HTMLResponse)
# async def read_home(request: Request):
#     return templates.TemplateResponse("home.html", {"request": request})