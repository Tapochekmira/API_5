import os
from itertools import count

import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable


def predict_rub_salary(salary_from, salary_to):
    if not (salary_from or salary_to):
        return None
    if not salary_from:
        return int(salary_to * 0.8)
    if not salary_to:
        return int(salary_from * 1.2)
    return (salary_to + salary_from) // 2


def predict_rub_salary_for_hh(salary):
    if not salary:
        return None
    if salary['currency'] != 'RUR':
        return None
    return predict_rub_salary(salary['from'], salary['to'])


def predict_rub_salary_for_sj(salary):
    if salary['currency'] != 'rub':
        return None
    return predict_rub_salary(salary['payment_from'], salary['payment_to'])


def create_average_language_salary_table(
        name_of_site,
        average_salary_by_language
):
    title = f'{name_of_site} Moscow'
    table_with_vacancies = [
        (
            'Язык программирования',
            'Вакансий найдено',
            'Вакансий обработано',
            'Средняя зарплата'
        )
    ]

    table_with_vacancies += [
        (
            language, vacancies_statistics['vacancies_found'],
            vacancies_statistics['vacancies_processed'],
            vacancies_statistics['average_salary']
        )
        for language, vacancies_statistics in
        average_salary_by_language.items()
    ]

    table_with_vacancies = AsciiTable(table_with_vacancies, title)
    table_with_vacancies.justify_columns[2] = 'right'
    return table_with_vacancies.table


def get_language_salary_hh(language):
    url = 'https://api.hh.ru/vacancies'
    number_of_moscow_for = 1
    age_of_oldest_vacancy = 30
    number_of_responses_per_page = 100
    sum_of_salaries = 0
    vacancies_processed = 0
    payload = {
        'text': f'Программист {language}',
        'area': number_of_moscow_for,
        'period': age_of_oldest_vacancy,
        'per_page': number_of_responses_per_page,
    }

    for page in count(0):
        payload['page'] = page
        response = requests.get(url, params=payload)
        response.raise_for_status()
        response = response.json()
        vacancies = response['items']

        for vacancy in vacancies:
            salary = predict_rub_salary_for_hh(vacancy['salary'])
            if salary:
                sum_of_salaries += salary
                vacancies_processed += 1

        if page >= response['pages'] - 1:
            break

    vacancies_found = response['found']
    return sum_of_salaries, vacancies_processed, vacancies_found


def get_average_salary_from_hh(programming_languages):
    average_salary_by_language = {}

    for language in programming_languages:
        sum_of_salaries, vacancies_processed, vacancies_found = \
            get_language_salary_hh(language)
        average_salary = None
        if vacancies_processed:
            average_salary = int(sum_of_salaries / vacancies_processed)

        average_salary_by_language[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary
        }

    return average_salary_by_language


def get_language_salary_sj(language, super_job_token):
    url = 'https://api.superjob.ru/2.0/vacancies'
    number_of_moscow_for = 4
    number_of_responses_per_page = 100
    sum_of_salaries = 0
    vacancies_processed = 0
    headers = {
        'X-Api-App-Id': super_job_token,
    }
    payload = {
        'town': number_of_moscow_for,
        'keyword': f'Программист {language}',
        'count': number_of_responses_per_page
    }

    for page in count(0):
        payload['page'] = page
        response = requests.get(url, headers=headers, params=payload)
        response.raise_for_status()

        response = response.json()
        vacancies = response['objects']
        for vacancy in vacancies:
            salary = predict_rub_salary_for_sj(vacancy)
            if salary:
                sum_of_salaries += salary
                vacancies_processed += 1

        if not response['more']:
            break

    vacancies_found = response['total']
    return sum_of_salaries, vacancies_processed, vacancies_found


def get_average_salary_from_sj(programming_languages, super_job_token):
    average_salary_by_language = {}

    for language in programming_languages:
        sum_of_salaries, vacancies_processed, vacancies_found = \
            get_language_salary_sj(language, super_job_token)
        average_salary = None
        if vacancies_processed:
            average_salary = int(sum_of_salaries / vacancies_processed)

        average_salary_by_language[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary
        }
    return average_salary_by_language


if __name__ == '__main__':
    load_dotenv()
    programming_languages = [
        'JavaScript',
        'Java',
        'Python',
        'Ruby',
        'C++',
        'C#',
        'C',
        'Go'
    ]
    super_job_token = os.environ['SUPER_JOB_TOKEN']
    print(
        create_average_language_salary_table(
            'HH.ru',
            get_average_salary_from_hh(programming_languages)
        )
    )
    print(
        create_average_language_salary_table(
            'SJ.ru',
            get_average_salary_from_sj(
                programming_languages,
                super_job_token)
        )
    )
