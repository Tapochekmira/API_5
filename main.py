import os
import requests
from pprint import pprint
from math import ceil
from terminaltables import AsciiTable
from dotenv import load_dotenv


def predict_rub_salary(salary_from, salary_to):
    if not(salary_from or salary_to):
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


def get_language_salary_hh(language):
    url = 'https://api.hh.ru/vacancies'
    sum_of_salaryes = 0
    vacancies_processed = 0
    
    payload = {
            'text': f'Программист {language}',
            'area': 1,
            'period': 30,
            'only_with_salary': 'true',
        }

    response = requests.get(url, params=payload)
    response.raise_for_status()
    vacancies_found = response.json()['found']
    pages = response.json()['pages']
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
    return sum_of_salaryes, vacancies_processed, vacancies_found

    
def get_average_salary_from_hh(programming_languages):
    number_of_vacancies_by_language = {} 

    for language in programming_languages:
        sum_of_salaryes, vacancies_processed, vacancies_found = get_language_salary_hh(language)
        average_salary = int(sum_of_salaryes / vacancies_processed)
        
        number_of_vacancies_by_language[language] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": vacancies_processed,
            "average_salary": average_salary
        }
        
    return number_of_vacancies_by_language


def get_language_salary_sj(language, super_job_token):
    url = 'https://api.superjob.ru/2.0/vacancies'
    headers = {
        'X-Api-App-Id': super_job_token,
    }
    payload = {
            'town': 4,
            'keyword': f'Программист {language}',
    }
    sum_of_salaryes = 0
    vacancies_processed = 0
    
    response = requests.get(url, headers=headers, params=payload)
    response.raise_for_status()
    
    vacancies_found = response.json()['total']
    
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
    return sum_of_salaryes, vacancies_processed, vacancies_found


def get_average_salary_from_sj(programming_languages):
    super_job_token = os.environ['SUPER_JOB_API']

    number_of_vacancies_by_language = {}

    for language in programming_languages:
        sum_of_salaryes, vacancies_processed, vacancies_found = get_language_salary_sj(language, super_job_token)
        average_salary = None
        if vacancies_processed:
            average_salary = int(sum_of_salaryes / vacancies_processed)
        
        number_of_vacancies_by_language[language] = {
            "vacancies_found": vacancies_found, 
            "vacancies_processed": vacancies_processed,
            "average_salary": average_salary
        }
    return number_of_vacancies_by_language


if __name__ == '__main__':
    programming_languages = ['JavaScript'] # , 'Java', 'Python', 'Ruby', 'C++', 'C#', 'C', 'Go']

    load_dotenv()
    output_vacancies_as_table('HH.ru', get_average_salary_from_hh(programming_languages))
    output_vacancies_as_table('SJ.ru', get_average_salary_from_sj(programming_languages))
