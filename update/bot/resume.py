import requests
from bs4 import BeautifulSoup
import fake_useragent
import json
import re
import time
from urllib.parse import urlencode, urlunparse, urlparse
import sqlite3

def get_links(keyword, experience_filters=None, schedule_filters=None, education_filters=None, salary_from=None, salary_to=None):
    base_url = 'https://hh.ru/search/resume'
    params = {
        'text': keyword,
        'area': '1',
        'isDefaultArea': 'true',
        'exp_period': 'all_time',
        'logic': 'normal',
        'pos': 'full_text',
        'page': '0',
        'search_period': '0',
        'order_by': 'relevance',
        'filter_exp_period': 'all_time',
        'relocation': 'living_or_relocation',
        'gender': 'unknown',
        'job_search_status_changed_by_user': 'true'
    }

    # Добавление параметров зарплаты, если они указаны
    if salary_from is not None:
        params['salary_from'] = salary_from
    if salary_to is not None:
        params['salary_to'] = salary_to
    
    # Если оба значения зарплаты указаны, добавить параметр only_with_salary
    if salary_from is not None and salary_to is not None:
        params['label'] = 'only_with_salary'
    # Создание URL без experience, schedule и education фильтров
    url_parts = list(urlparse(base_url))
    query = urlencode(params)
    url_parts[4] = query

    # Добавление experience, schedule и education фильтров, если они указаны
    url = urlunparse(url_parts)
    if experience_filters:
        url += ''.join([f'&experience={exp}' for exp in experience_filters])
    if schedule_filters:
        url += ''.join([f'&schedule={sched}' for sched in schedule_filters])
    if education_filters:
        url += ''.join([f'&education_level={edu}' for edu in education_filters])
    print(url)
    user_agent = fake_useragent.UserAgent()
    
    try:
        response = requests.get(url, headers={'user-agent': user_agent.random})
        response.raise_for_status()  # проверка запроса
        soup = BeautifulSoup(response.content, 'lxml')
        # Находим количество страниц результатов
        pager = soup.find('div', class_='pager')
        if pager:
            page_count = int(pager.find_all('span', recursive=False)[-1].find('a').find('span').text)
        else:
            page_count = 1  # Если не найден блок пагинации, считаем что только одна страница
    except (requests.RequestException, ValueError, AttributeError) as e:
        print(f"Error during initial request: {e}")
        return
    
    for page in range(page_count):
        try:
            current_page_url = url + f'&page={page}'
            response = requests.get(current_page_url, headers={'user-agent': user_agent.random})
            response.raise_for_status()  
            soup = BeautifulSoup(response.content, 'lxml')
            links = [f"https://hh.ru{a['href'].split('?')[0]}"
                     for a in soup.find_all("a", attrs={"rel": "nofollow"}) 
                     if not a['href'].startswith('/search/resume')]
            
            for link in links:
                yield link
        except (requests.RequestException, AttributeError) as e:
            print(f'Error during page {page} request: {e}')
        time.sleep(1)

def get_resume(link):
    user_agent = fake_useragent.UserAgent()
    
    try:
        response = requests.get(link, headers={'user-agent': user_agent.random})
        response.raise_for_status()  # Проверяем успешность запроса
        soup = BeautifulSoup(response.content, "lxml")
        
        name = soup.find(attrs={"class": "resume-block__title-text"}).text if soup.find(attrs={"class": "resume-block__title-text"}) else ''
        salary = soup.find(attrs={"class": "resume-block__salary"}).text.replace("\u2009", "").replace('\xa0', ' ') if soup.find(attrs={"class": "resume-block__salary"}) else 'Не указана'
        tags = [tag.text for tag in soup.find(attrs={"class": "bloko-tag-list"}).find_all(attrs={"class": "bloko-tag__section_text"})] if soup.find(attrs={"class": "bloko-tag-list"}) else ['Отсутствует']
        sex = soup.find(attrs={'data-qa': 'resume-personal-gender'}).text if soup.find(attrs={'data-qa': 'resume-personal-gender'}) else 'Не указан'
        experience = soup.find(attrs={'class': 'resume-block__title-text_sub'}).text.replace('\xa0', ' ').replace('Ключевые навыки','Не указан').replace('Key skills', 'Не указан') if soup.find(attrs={'class': 'resume-block__title-text_sub'}) else ''
        age = soup.find(attrs={'data-qa': 'resume-personal-age'}).text.replace('\xa0', ' ') if soup.find(attrs={'data-qa': 'resume-personal-age'}) else 'Не указан'
        employment_text = None
        schedule_text = None

        all_paragraphs = soup.find_all('p')

        for p in all_paragraphs:
            if 'Занятость:' in p.text:
                employment_text = p.text.strip().replace('Занятость: ', '')
                break
        if employment_text:
            employment_list = [e.strip() for e in employment_text.split(',')]
        else:
            employment_list = ['Информация о занятости не найдена']
        
        for p in all_paragraphs:
            if 'График работы:' in p.text:
                schedule_text = p.text.strip().replace('График работы: ', '')
                break
        if schedule_text:
            schedule_list = [e.strip() for e in schedule_text.split(',')]
        else:
            schedule_list = ['Информация о графике работы не найдена']

        resume = {
            "name": name,
            "sex": sex,
            "age": age,
            "salary": salary,
            "experience": experience,
            "tags": tags,
            'employment_list':employment_list,
            'schedule_list':schedule_list,
            'link':link
        }
        return resume
    except (requests.RequestException, AttributeError) as e:
        print(f'Error fetching resume from {link}: {e}')
        return None
    
def insert_resume(cursor, keyword, resume):
    cursor.execute(f'''SELECT id FROM {keyword} WHERE name=? AND sex=? AND age=? AND salary=? AND experience=? AND tags=? AND employment=? AND schedule=? AND link=?''',
                   (resume['name'], resume['sex'], resume['age'], resume['salary'], resume['experience'], ', '.join(resume['tags']), ', '.join(resume['employment_list']), ', '.join(resume['schedule_list']), resume['link']))
    if cursor.fetchone() is None:
        cursor.execute(f'''INSERT INTO {keyword} (name, sex, age, salary, experience, tags, employment, schedule, link)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (resume['name'], resume['sex'], resume['age'], resume['salary'], resume['experience'],
                        ', '.join(resume['tags']), ', '.join(resume['employment_list']), ', '.join(resume['schedule_list']), resume['link']))
        return True
    return False

