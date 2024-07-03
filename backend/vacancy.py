import requests
from bs4 import BeautifulSoup
import fake_useragent
import sqlite3
import time

def get_links(keyword, education_filters=None, salary = None, schedule_filters=None, experience=None, offset=0):
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
        params.extend(f'education={edu}' for edu in education_filters)

    if salary:
        params.append(f'salary={salary}')
        params.append('only_with_salary=true')
    elif salary is not None:
        params.append('only_with_salary=false')

    if schedule_filters:
        params.extend(f'schedule={schedule}' for schedule in schedule_filters)
    
    if experience:
        experience = str(experience).replace("['",'').replace("']",'')
        params.append(f'experience={experience}')

    url = base_url + '&'.join(params)
    print(url)
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

        for page in range(offset, page_count):
            try:
                page_url = f'{url}&page={page}'
                response = requests.get(page_url, headers={'user-agent': user_agent.random})
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'lxml')
                for a in soup.find_all('a', attrs={'class': 'bloko-link'}):
                    href = a.get('href', '').split('?')[0]
                    if '/vacancy/' in href:
                        yield href
            except (requests.RequestException, AttributeError) as e:
                print(f'Error during page {page} request: {e}')
                continue
            time.sleep(1)
    except (requests.RequestException, ValueError, AttributeError) as e:
        print(f"Error during initial request: {e}")

def get_vacancy(link, education_filters):
    user_agent = fake_useragent.UserAgent()

    try:
        response = requests.get(link, headers={'user-agent': user_agent.random})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "lxml")

        title_elem = soup.find(attrs={"class": "bloko-header-section-1"})
        title = title_elem.text if title_elem else 'Не указано'
        
        name_elem = soup.find('a', attrs={'data-qa': 'vacancy-company-name'})
        name = name_elem.text.replace('\xa0', ' ') if name_elem else 'Не указано'
        
        salary_elem = soup.find('div', attrs={"data-qa": "vacancy-salary"})
        salary = salary_elem.text if salary_elem else 'Не указана'
        
        tags_elems = soup.find_all(attrs={"data-qa": "skills-element"})
        tags = [tag.text for tag in tags_elems] if tags_elems else ['Не указаны']
        
        experience_elem = soup.find(attrs={"data-qa": "vacancy-experience"})
        experience = experience_elem.text if experience_elem else 'Не указан'
        
        busyness_elem = soup.find(attrs={"data-qa": "vacancy-view-employment-mode"})
        busyness = busyness_elem.text if busyness_elem else 'Не указана'

        if 'higher' in education_filters:
            education = 'Высшее'
        elif 'special_secondary' in education_filters:
            education = 'Среднее профессиональное'
        elif 'not_required_or_not_specified' in education_filters:
            education = 'Не указано или не нужно'
        else:
            education = 'Не указано или не нужно'  # В случае отсутствия фильтров по образованию

        if title == 'Не указано':
            return None
        else:
            return {
                'title': title,
                'name': name,
                'tags': tags,
                'salary': salary,
                'experience': experience,
                'busyness': busyness,
                'education': education,
                'link': link
            }
    except (requests.RequestException, AttributeError) as e:
        print(f'Error fetching vacancy from {link}: {e}')
        return None

def insert_vacancy(cursor, table_name, vacancy):
    cursor.execute(f'''SELECT id FROM {table_name} WHERE title=? AND company=? AND salary=? AND experience=? AND busyness=? AND education=? AND link=?''',
                   (vacancy['title'], vacancy['name'], vacancy['salary'], vacancy['experience'], vacancy['busyness'], vacancy['education'], vacancy['link']))
    if cursor.fetchone() is None:
        cursor.execute(f'''INSERT INTO {table_name} (title, company, salary, experience, busyness, education, link)
                           VALUES (?, ?, ?, ?, ?, ?, ?)''',
                       (vacancy['title'], vacancy['name'], vacancy['salary'], vacancy['experience'], vacancy['busyness'], vacancy['education'], vacancy['link']))
        return True
    return False
