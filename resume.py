import requests
from bs4 import BeautifulSoup
import fake_useragent
import json
import time
from urllib.parse import urlencode, urlunparse, urlparse

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
    
    user_agent = fake_useragent.UserAgent()
    
    try:
        response = requests.get(url, headers={'user-agent': user_agent.random})
        response.raise_for_status()  # проверка запроса
        soup = BeautifulSoup(response.content, 'lxml')
        page_count = int(soup.find('div', class_='pager').find_all('span', recursive=False)[-1].find('a').find('span').text)
    except (requests.RequestException, ValueError, AttributeError) as e:
        print(f"Error during initial request: {e}")
        return
    
    for page in range(page_count):
        try:
            url = url + f'&page={page}'
            response = requests.get(url, headers={'user-agent': user_agent.random})
            response.raise_for_status()  
            print(url)
            soup = BeautifulSoup(response.content, 'lxml')
            links = [f"https://hh.ru{a['href'].split('?')[0]}"
                     for a in soup.find_all("a", attrs={"rel": "nofollow"}) 
                     if not a['href'].startswith('/search/resume')]
            
            #удаление ненужных ссылок
            for link in links[1:-7]:
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
        salary = soup.find(attrs={"class": "resume-block__salary"}).text.replace("\u2009", "").replace('\xa0', ' ') if soup.find(attrs={"class": "resume-block__salary"}) else ''
        tags = [tag.text for tag in soup.find(attrs={"class": "bloko-tag-list"}).find_all(attrs={"class": "bloko-tag__section_text"})] if soup.find(attrs={"class": "bloko-tag-list"}) else []
        sex = soup.find(attrs={'data-qa': 'resume-personal-gender'}).text if soup.find(attrs={'data-qa': 'resume-personal-gender'}) else ''
        skill = soup.find(attrs={'class': 'resume-block__title-text_sub'}).text.replace('\xa0', ' ') if soup.find(attrs={'class': 'resume-block__title-text_sub'}) else ''
        age = soup.find(attrs={'data-qa': 'resume-personal-age'}).text.replace('\xa0', ' ') if soup.find(attrs={'data-qa': 'resume-personal-age'}) else ''
        
        resume = {
            "name": name,
            "sex": sex,
            "age": age,
            "salary": salary,
            "skill": skill,
            "tags": tags,
        }
        return resume
    except (requests.RequestException, AttributeError) as e:
        print(f'Error fetching resume from {link}: {e}')
        return None

if __name__ == "__main__": 
    data = []
    keyword = "python"
    experience_filters = ["between1And3", "noExperience", "moreThan6", "between3And6"]
    schedule_filters = ["fullDay", "remote", "flexible", "shift", "flyInFlyOut"]
    education_filters = ["higher", "unfinished_higher", "master", "bachelor", "special_secondary"]
    salary_from = 100000
    salary_to = 200000
    links = get_links(keyword, experience_filters, schedule_filters, education_filters, salary_from, salary_to)
    for link in links: # чисто условность, пользователь пишет что-то вместо python
        resume = get_resume(link)
        if resume:
            data.append(resume)
            time.sleep(0.5) 
            with open('resume.json', 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
