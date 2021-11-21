import os
import requests
from pprint import pprint
from math import ceil
from terminaltables import AsciiTable
from dotenv import load_dotenv


def predict_rub_salary(currency, salary_from, salary_to):
    if currency != 'RUR' and currency != 'rub':
        return None
    if not(salary_from or salary_to):
        return None
    if not salary_from:
        return int(salary_to * 0.8)
    if not salary_to:
        return int(salary_from * 1.2)
    return (salary_to + salary_from) // 2


def predict_rub_salary_for_hh(vacancy):
    currency = vacancy['currency']
    return predict_rub_salary(currency, vacancy['from'], vacancy['to'])


def predict_rub_salary_for_sj(vacancy):
    if not (vacancy['payment_to'] or vacancy['payment_from']):
        return None
    currency = vacancy['currency']
    return predict_rub_salary(currency, vacancy['payment_from'], vacancy['payment_to'])


def output_vacancies_as_table(name_of_site, number_of_vacancies_by_language):
    title = f'{name_of_site} Moscow'  
    table_data = [
        (
            'Язык программирования', 
            'Вакансий найдено',
            'Вакансий обработано',
            'Средняя зарплата'
        )
    ]

    table_data += [(language, result['vacancies_found'], 
                   result['vacancies_processed'],
                   result['average_salary'])
                  for language, result in 
                  number_of_vacancies_by_language.items()]
    table_instance = AsciiTable(table_data, title)
    table_instance.justify_columns[2] = 'right'
    print(table_instance.table)


def get_salary_from_hh():
    url = 'https://api.hh.ru/vacancies'
    number_of_vacancies_by_language = {} 


    for language in programming_languages:
        payload = {
            'text': f'Программист {language}',
            'area': 1,
            'period': 30,
            'only_with_salary': 'true',
        }

        response = requests.get(url, params=payload)
        response.raise_for_status()
        number_of_vacancies_by_language[language] = {
            "vacancies_found": response.json()['found']
        }
        pages = response.json()['pages']

        sum_of_salaryes = 0
        vacancies_processed = 0
        for page in range(pages):
            payload = {
                'text': f'Программист {language}',
                'area': 1,
                'period': 30,
                'only_with_salary': 'true',
                'page': page
            }
            response = requests.get(url, params=payload)
            response.raise_for_status()
            
            vacancies = response.json()['items']
            for vacancy in vacancies:
                salary = predict_rub_salary_for_hh(vacancy['salary'])
                if salary:
                    sum_of_salaryes += salary 
                    vacancies_processed += 1
        average_salary = int(sum_of_salaryes / vacancies_processed)

        number_of_vacancies_by_language[language].update(
            {
            "vacancies_processed": vacancies_processed
        })
        number_of_vacancies_by_language[language].update(
            {
            "average_salary": average_salary
        })
    output_vacancies_as_table('HH.ru', number_of_vacancies_by_language)


def get_salary_from_sj():
    url = 'https://api.superjob.ru/2.0/vacancies'
    super_job_token = os.environ['SUPER_JOB_API']
    headers = {
        'X-Api-App-Id': super_job_token,
    }

    number_of_vacancies_by_language = {}


    for language in programming_languages:
        payload = {
            'town': 4,
            'keyword': f'Программист {language}',
        }
        response = requests.get(url, headers=headers, params=payload)
        response.raise_for_status()
        vacancies_found = response.json()['total']
        

        sum_of_salaryes = 0
        vacancies_processed = 0
        pages = ceil(vacancies_found / 100)
        for page in range(pages):
            payload = {
                'town': 4,
                'keyword': f'Программист {language}',
                'page': page,
                'count': 100
            }
            response = requests.get(url, headers=headers, params=payload)
            response.raise_for_status()
            vacancies = response.json()['objects']
            for vacancy in vacancies:
                salary = predict_rub_salary_for_sj(vacancy) 
                if salary:
                    sum_of_salaryes += salary 
                    vacancies_processed += 1

        average_salary = None
        if vacancies_processed != 0:
            average_salary = int(sum_of_salaryes / vacancies_processed)
        
        number_of_vacancies_by_language[language] = {
            "vacancies_found": vacancies_found 
        }

        number_of_vacancies_by_language[language].update(
            {
            "vacancies_processed": vacancies_processed
        })
        number_of_vacancies_by_language[language].update(
            {
            "average_salary": average_salary
        })
    output_vacancies_as_table('Super Job', number_of_vacancies_by_language)


if __name__ == '__main__':
    load_dotenv()
    get_salary_from_hh()
    get_salary_from_sj()
