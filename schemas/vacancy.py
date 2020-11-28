from typing import List, Optional

from pydantic import BaseModel


class VacancyBase(BaseModel):
    title: str
    url: str


class Vacancy(VacancyBase):
    pass


class VacancyList(BaseModel):
    vacancies: List[Vacancy]
