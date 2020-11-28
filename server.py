import asyncio

import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from config import VACANCIES_HOST
from services.resume_analyzer_service import ResumeAnalyzer
from services.vacancies_service import VacanciesService

resume_analyzer = ResumeAnalyzer()
vacancies_service = VacanciesService(VACANCIES_HOST)

resume_analyzer.update_tfidf_values()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post('/get-relevant-vacancies', tags=['public'])
async def get_relevant_vacancies(resume: UploadFile = File(...)):
    resume_text = await resume.read()
    resume_text = resume_text.decode("utf8")
    vacancies = resume_analyzer.get_vacancies_urls(resume_text)
    return vacancies


@app.get('/upload-vacancies', tags=['internal'])
async def upload_vacancies_to_json():
    try:
        await vacancies_service.upload_vacancies()
    except Exception as e:
        return {
            'status': 'fail',
            'errors': str(e)
        }
    return {'status': 'ok'}


@app.post('/seed-vacancies-db', tags=['internal'])
async def seed_vacancies_for_db():
    try:
        results = await vacancies_service.seed_vacancies_db()
    except Exception as e:
        return {
            'status': 'fail',
            'errors': str(e)
        }
    return results


@app.post('/update-analyzer', tags=['internal'])
async def update_analyzer_data():
    try:
        resume_analyzer.update_tfidf_values()
    except Exception as e:
        return {
            'status': 'fail',
            'errors': str(e)
        }
    return {'status': 'ok'}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
