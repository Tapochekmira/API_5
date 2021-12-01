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


def predict_rub_salary_for_hh(vacancy):
    if vacancy['currency'] != 'RUR':
        return None
    return predict_rub_salary(vacancy['from'], vacancy['to'])


def predict_rub_salary_for_sj(vacancy):
    if not (vacancy['payment_to'] or vacancy['payment_from']):
        return None
    if vacancy['currency'] != 'rub':
        return None
    return predict_rub_salary(vacancy['payment_from'], vacancy['payment_to'])


def converting_the_vacancy_list_into_a_table(
        name_of_site,
        number_of_vacancies_by_language
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

    table_with_vacancies += [(language, number['vacancies_found'],
                              number['vacancies_processed'],
                              number['average_salary'])
                             for language, number in
                             number_of_vacancies_by_language.items()]
    table_instance = AsciiTable(table_with_vacancies, title)
    table_instance.justify_columns[2] = 'right'
    return table_instance.table


def get_language_salary_hh(language):
    url = 'https://api.hh.ru/vacancies'
    sum_of_salaries = 0
    vacancies_processed = 0

    for page in count(0):
        payload = {
            'text': f'Программист {language}',
            'area': 1,
            'period': 30,
            'only_with_salary': 'true',
            'per_page': 100,
            'page': page
        }
        response = requests.get(url, params=payload)
        response.raise_for_status()

        response = response.json()
        vacancies_found = response['found']
        vacancies = response['items']

        for vacancy in vacancies:
            salary = predict_rub_salary_for_hh(vacancy['salary'])
            if salary:
                sum_of_salaries += salary
                vacancies_processed += 1
        if page >= response['pages']:
            break

    return sum_of_salaries, vacancies_processed, vacancies_found


def get_average_salary_from_hh(programming_languages):
    number_of_vacancies_by_language = {}

    for language in programming_languages:
        sum_of_salaries, vacancies_processed, vacancies_found = \
            get_language_salary_hh(language)
        average_salary = int(sum_of_salaries / vacancies_processed)

        number_of_vacancies_by_language[language] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": vacancies_processed,
            "average_salary": average_salary
        }

    return number_of_vacancies_by_language


def get_language_salary_sj(language, super_job_token):
    url = 'https://api.superjob.ru/2.0/vacancies'
    sum_of_salaries = 0
    vacancies_processed = 0

    for page in count(0):
        headers = {
            'X-Api-App-Id': super_job_token,
        }
        payload = {
            'town': 4,
            'keyword': f'Программист {language}',
            'page': page,
            'count': 100
        }
        response = requests.get(url, headers=headers, params=payload)
        response.raise_for_status()

        response = response.json()
        vacancies_found = response['total']
        vacancies = response['objects']
        for vacancy in vacancies:
            salary = predict_rub_salary_for_sj(vacancy)
            if salary:
                sum_of_salaries += salary
                vacancies_processed += 1

        if not response['more']:
            break

    return sum_of_salaries, vacancies_processed, vacancies_found


def get_average_salary_from_sj(programming_languages, super_job_token):
    number_of_vacancies_by_language = {}

    for language in programming_languages:
        sum_of_salaries, vacancies_processed, vacancies_found = \
            get_language_salary_sj(language, super_job_token)
        average_salary = None
        if vacancies_processed:
            average_salary = int(sum_of_salaries / vacancies_processed)

        number_of_vacancies_by_language[language] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": vacancies_processed,
            "average_salary": average_salary
        }
    return number_of_vacancies_by_language


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
    super_job_token = os.environ['SUPER_JOB_API']
    print(
        converting_the_vacancy_list_into_a_table(
            'HH.ru',
            get_average_salary_from_hh(programming_languages)
        )
    )
    print(
        converting_the_vacancy_list_into_a_table(
            'SJ.ru',
            get_average_salary_from_sj(
                programming_languages,
                super_job_token)
        )
    )
