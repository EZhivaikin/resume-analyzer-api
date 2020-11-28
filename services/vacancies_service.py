import asyncio
import json
from typing import List

from async_request import async_request


class VacanciesService:
    def __init__(self, host: str):
        self._host = host

    async def upload_vacancies(self):
        path = '/api/vacancies'
        data = await self._get_vacancies(path)
        with open('vacancies-from-service.json', 'w') as fp:
            json.dump(data, fp)

    async def seed_vacancies_db(self):
        path = '/api/vacancies'
        data = self._prepare_vacancies_data()
        vacancies = await self._get_vacancies(path)
        if len(vacancies) > 50:
            return
        results = await self._load_vacancies_to_service(path, data)
        successful_count = 0
        fail_count = 0
        for result in results:
            if result['successful']:
                successful_count += 1
            else:
                fail_count += 1
        return {'success': successful_count, 'fail': fail_count}

    async def _get_vacancies(self, path):
        url = f'{self._host}{path}'
        data = await async_request(url=url, method='GET')
        return data['data']

    async def _load_vacancies_to_service(self, path: str, vacancies: List[dict]):
        url = f'{self._host}{path}'
        futures = [
            async_request(
                url=url, method='POST', data=json.dumps(vacancy), headers={'Content-Type': 'application/json'}
            )
            for vacancy in vacancies
        ]
        states = []
        for future in asyncio.as_completed(futures):
            result = await future
            states.append(result)
        return states

    def _prepare_vacancies_data(self):
        data = list()
        with open('vacancies.json') as f:
            vacancies = json.load(f)
        for vacancy in vacancies:
            skills_str = ' '.join(skill['name'] for skill in vacancy['key_skills'])
            description = vacancy['description']
            title = vacancy['name']
            text = f"{description}\nКлючевые навыки: {skills_str}"
            data.append(dict(name=title, description=text))

        return data