import re
import ssl
from typing import List

import nltk
import requests
from nltk.corpus import stopwords
from pymystem3 import Mystem
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.metrics.pairwise import cosine_similarity

from config import VACANCIES_HOST
from schemas.vacancy import VacancyList, Vacancy


class ResumeAnalyzer:
    def __init__(self):
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context

        nltk.download("stopwords")
        self._stem = Mystem()
        self._count_vectorizer = CountVectorizer()
        self._tfidf_transformer = TfidfTransformer()

    def update_tfidf_values(self):
        path = '/api/vacancies'
        self._vacancies = requests.get(f"{VACANCIES_HOST}{path}").json()['data']
        if len(self._vacancies) == 0:
            return
        docs = []
        for vacancy in self._vacancies:
            # skills_str = ' '.join(skill['name'] for skill in vacancy['key_skills'])
            description = vacancy['description']
            title = vacancy['name']
            # text = f"{description} {skills_str} {title}"
            text = f"{description} {title}"
            docs.append(self._preprocess_resume_text(text))

        X = self._count_vectorizer.fit_transform(docs)
        del docs
        self._docs_idfs_vector = self._tfidf_transformer.fit_transform(X)
        self._vacancies_ids = [vacancy['id'] for vacancy in self._vacancies]

    def get_vacancies_urls(self, text: str) -> VacancyList:
        processed_text = self._preprocess_resume_text(text)
        resume_vals = self._count_vectorizer.transform([processed_text])
        resume_idfs = self._tfidf_transformer.transform(resume_vals)
        cosine_similarities = cosine_similarity(resume_idfs, self._docs_idfs_vector).flatten()
        relevant_vacancies = self._get_top_five_ids(cosine_similarities)
        keywords = self._get_keywords(resume_idfs)
        vacancies = [
            Vacancy(
                id=vacancy['id'],
                title=vacancy['name'],
                url=f"{VACANCIES_HOST}/api/vacancies/{vacancy['id']}",
            ) for vacancy in relevant_vacancies
        ]
        vacancy_list = VacancyList(vacancies=vacancies, keywords=keywords)

        return vacancy_list

    def _get_top_five_ids(self, cosine_similarities) -> List[dict]:
        similarities = list(zip(self._vacancies, cosine_similarities))
        similarities.sort(key=lambda x: x[1], reverse=True)
        vacancies: List[dict] = [sim[0] for sim in similarities[:5]]
        return vacancies

    def _preprocess_resume_text(self, text: str) -> str:
        stop_words = stopwords.words("russian")
        doc = re.sub('<[^>]*>', '', text.lower())
        doc = re.sub('&quot;', '', doc)
        doc = re.sub(r'[^a-zа-я]+', ' ', doc, re.UNICODE)

        doc = doc.strip()
        doc = doc.replace('\u200b', ' ')
        doc = doc.replace('•', ' ')
        doc = doc.replace('-', ' ')
        doc = doc.replace('.', ' ')
        doc = doc.replace(',', ' ')
        doc = doc.replace('(', ' ')
        doc = doc.replace(')', ' ')
        doc = doc.replace('\n', ' ')

        words = self._stem.lemmatize(doc.lower())
        words = [word for word in words if word not in stop_words]
        return ' '.join(words)

    def _get_keywords(self, resume_idfs):
        words_idfs = list(zip(self._count_vectorizer.get_feature_names(), resume_idfs.toarray()[0]))
        words_idfs.sort(key=lambda x: x[1], reverse=True)
        keywords = [word[0] for word in words_idfs]
        return keywords
