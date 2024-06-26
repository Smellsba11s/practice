import requests
from bs4 import BeautifulSoup
import fake_useragent
import json
import time
import sqlite3

def get_links(keyword, education_filters=None, salary=None, schedule_filters=None, experience=None):
    base_url = 'https://hh.ru/search/vacancy?'

    params = [
        'area=1',
        'hhtmFrom=resume_search_result',
        'hhtmFromLabel=vacancy_search_line',
        'search_field=name',
        'search_field=company_name',
        'search_field=description',
        'enable_snippets=false',
        f'text={keyword}'
    ]

    if education_filters:
        for edu in education_filters:
            params.append(f'education={edu}')

    if salary:
        params.append(f'salary={salary}')
        params.append('only_with_salary=true')
    elif salary is not None:
        params.append('only_with_salary=false')

    if schedule_filters:
        for schedule in schedule_filters:
            params.append(f'schedule={schedule}')

    if experience:
        params.append(f'experience={experience}')

    url = base_url + '&'.join(params)
    user_agent = fake_useragent.UserAgent()

    try:
        response = requests.get(url, headers={'user-agent': user_agent.random})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')

        pager = soup.find('div', class_='pager')
        if pager:
            page_count = int(pager.find_all('span', recursive=False)[-1].find('a').find('span').text)
        else:
            page_count = 1

        for page in range(page_count):
            try:
                page_url = f'{url}&page={page}'
                print(page_url)
                response = requests.get(page_url, headers={'user-agent': user_agent.random})
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'lxml')
                for a in soup.find_all('a', attrs={'class': 'bloko-link'}):
                    href = a.attrs['href'].split('?')[0]
                    if '/vacancy/' in href:
                        yield href
            except (requests.RequestException, AttributeError) as e:
                print(f'Error during page {page} request: {e}')
            time.sleep(1)
    except (requests.RequestException, ValueError, AttributeError) as e:
        print(f"Error during initial request: {e}")

def get_vacancy(link):
    user_agent = fake_useragent.UserAgent()

    try:
        response = requests.get(link, headers={'user-agent': user_agent.random})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "lxml")

        title = soup.find(attrs={"class": "bloko-header-section-1"}).text if soup.find(attrs={"class": "bloko-header-section-1"}) else 'Не указано'
        name = soup.find('a', attrs={'data-qa': 'vacancy-company-name'}).text.replace('\xa0', ' ') if soup.find('a', attrs={'data-qa': 'vacancy-company-name'}) else 'Не указано'
        salary = soup.find('div', attrs={"data-qa": "vacancy-salary"}).text if soup.find('div', attrs={"data-qa": "vacancy-salary"}) else 'Не указана'
        tags = [tag.text for tag in soup.find(attrs={"class": "vacancy-skill-list--COfJZoDl6Y8AwbMFAh5Z"}).find_all(attrs={"data-qa": "skills-element"})] if soup.find(attrs={"class": "vacancy-skill-list--COfJZoDl6Y8AwbMFAh5Z"}) else ['Не указаны']
        experience = soup.find(attrs={"data-qa": "vacancy-experience"}).text if soup.find(attrs={"data-qa": "vacancy-experience"}) else 'Не указан'
        busyness = soup.find(attrs={"data-qa": "vacancy-view-employment-mode"}).text if soup.find(attrs={"data-qa": "vacancy-view-employment-mode"}) else 'Не указана'

        resume = {
            'title': title,
            'name': name,
            'tags': tags,
            'salary': salary,
            'experience': experience,
            'busyness': busyness,
            'link': link
        }
        if title == 'Не указано':
            return None
        else:
            return resume
    except (requests.RequestException, AttributeError) as e:
        print(f'Error fetching resume from {link}: {e}')
        return None

def insert_vacancy(cursor, table_name, vacancy):
    cursor.execute(f'''SELECT id FROM {table_name} WHERE title=? AND company=? AND salary=? AND experience=? AND busyness=? AND link=?''',
                   (vacancy['title'], vacancy['name'], vacancy['salary'], vacancy['experience'], vacancy['busyness'], vacancy['link']))
    if cursor.fetchone() is None:
        cursor.execute(f'''INSERT INTO {table_name} (title, company, salary, experience, busyness, link)
                           VALUES (?, ?, ?, ?, ?, ?)''',
                       (vacancy['title'], vacancy['name'], vacancy['salary'], vacancy['experience'], vacancy['busyness'], vacancy['link']))
        return True
    return False

if __name__ == "__main__":
    data = []
    keyword = "сварщик"
    education_filters = ["higher", 'special_secondary', 'not_required_or_not_specified']
    salary = 50000
    schedule_filters = ["fullDay", "remote", "flexible", "shift"]
    experience = "between1And3"

    conn = sqlite3.connect('bd_vacancy/vacancy.db')
    cursor = conn.cursor()
    cursor.execute(f'''CREATE TABLE IF NOT EXISTS {keyword}
                       (id INTEGER PRIMARY KEY, title TEXT, company TEXT, salary TEXT, experience TEXT, busyness TEXT, link TEXT)''')
    cursor.execute(f'''CREATE UNIQUE INDEX IF NOT EXISTS idx_{keyword}_unique 
                       ON {keyword} (title, company, salary, experience, busyness, link)''')

    conn.commit()
    for link in get_links(keyword, education_filters, salary, schedule_filters, experience):
        vacancy = get_vacancy(link)
        if vacancy:
            data.append(vacancy)
            time.sleep(0.5)
            with open('vacancy.json', 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
            with open('vacancy.json', 'r', encoding='utf-8') as json_file:
                vacancies_data = json.load(json_file)
            for vacancy in vacancies_data:
                if insert_vacancy(cursor, keyword, vacancy):
                    conn.commit()
    conn.close()