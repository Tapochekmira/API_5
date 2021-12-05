import os
from itertools import count

import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable

NUMBER_OF_MOSCOW_FOR_HH = 1
AGE_OF_OLDEST_VACANCY_HH = 30
NUMBER_OF_RESPONSES_PER_PAGE_HH = 100
NUMBER_OF_MOSCOW_FOR_SJ = 4
NUMBER_OF_RESPONSES_PER_PAGE_SJ = 100


def predict_rub_salary(salary_from, salary_to):
    if not (salary_from or salary_to):
        return None
    if not salary_from:
        return int(salary_to * 0.8)
    if not salary_to:
        return int(salary_from * 1.2)
    return (salary_to + salary_from) // 2


def predict_rub_salary_for_hh(vacancy):
    if vacancy['currency'] != 'RUR':
        return None
    return predict_rub_salary(vacancy['from'], vacancy['to'])


def predict_rub_salary_for_sj(vacancy):
    if vacancy['currency'] != 'rub':
        return None
    return predict_rub_salary(vacancy['payment_from'], vacancy['payment_to'])


def creating_table_average_salary_by_language(
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

    table_with_vacancies += [(language, vacancies_information['vacancies_found'],
                              vacancies_information['vacancies_processed'],
                              vacancies_information['average_salary'])
                             for language, vacancies_information in
                             average_salary_by_language.items()]

    table_with_vacancies = AsciiTable(table_with_vacancies, title)
    table_with_vacancies.justify_columns[2] = 'right'
    return table_with_vacancies.table


def get_language_salary_hh(language):
    url = 'https://api.hh.ru/vacancies'
    sum_of_salaries = 0
    vacancies_processed = 0
    payload = {
        'text': f'Программист {language}',
        'area': NUMBER_OF_MOSCOW_FOR_HH,
        'period': AGE_OF_OLDEST_VACANCY_HH,
        'only_with_salary': 'true',
        'per_page': NUMBER_OF_RESPONSES_PER_PAGE_HH,
    }
    for page in count(0):
        payload['page'] = page
        response = requests.get(url, params=payload)
        response.raise_for_status()
        response = response.json()
        if page >= response['pages']:
            break

        vacancies = response['items']
        for vacancy in vacancies:
            salary = predict_rub_salary_for_hh(vacancy['salary'])
            if salary:
                sum_of_salaries += salary
                vacancies_processed += 1

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
    sum_of_salaries = 0
    vacancies_processed = 0
    headers = {
        'X-Api-App-Id': super_job_token,
    }
    payload = {
        'town': NUMBER_OF_MOSCOW_FOR_SJ,
        'keyword': f'Программист {language}',
        'count': NUMBER_OF_RESPONSES_PER_PAGE_SJ
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
        creating_table_average_salary_by_language(
            'HH.ru',
            get_average_salary_from_hh(programming_languages)
        )
    )
    print(
        creating_table_average_salary_by_language(
            'SJ.ru',
            get_average_salary_from_sj(
                programming_languages,
                super_job_token)
        )
    )
