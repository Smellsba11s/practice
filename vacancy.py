import requests
from bs4 import BeautifulSoup
import fake_useragent
import json
import time
from urllib.parse import urlencode, urlunparse, urlparse

def get_links(keyword, education_filters=None, salary=None, part_time_filters=None, experience=None):
    base_url = 'https://hh.ru/search/vacancy?'

    # Создаем список для параметров
    params = []

    # Добавляем основные параметры
    params.append('area=1')
    params.append('hhtmFrom=resume_search_result')
    params.append('hhtmFromLabel=vacancy_search_line')
    params.append('search_field=name')
    params.append('search_field=company_name')
    params.append('search_field=description')
    params.append('enable_snippets=false')
    params.append(f'text={keyword}')

    # Добавление фильтра по образованию, если указан
    if education_filters:
        for edu in education_filters:
            params.append(f'education={edu}')

    # Добавление фильтра по зарплате, если указана
    if salary:
        params.append(f'salary={salary}')
        params.append('only_with_salary=true')  # Если указана зарплата, то автоматически true для only_with_salary
    elif salary is not None:
        params.append('only_with_salary=false')  # Если salary явно указан как None, то устанавливаем false для only_with_salary

    # Добавление фильтров по частичной занятости, если указаны
    if part_time_filters:
        for pt in part_time_filters:
            params.append(f'part_time={pt}')

    # Добавление фильтра по опыту работы, если указан
    if experience:
        params.append(f'experience={experience}')

    # Собираем окончательный URL
    url = base_url + '&'.join(params)
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

        # Перебираем все страницы результатов
        for page in range(page_count):
            try:
                page_url = f'{url}&page={page}'
                print(page_url)
                response = requests.get(page_url, headers={'user-agent': user_agent.random})
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'lxml')
                for a in soup.find_all('a', attrs={'class':'bloko-link'}):
                    href = a.attrs['href'].split('?')[0]
                    if '/vacancy/' in href:
                        yield href
            except (requests.RequestException, AttributeError) as e:
                print(f'Error during page {page} request: {e}')
            time.sleep(1)
    except (requests.RequestException, ValueError, AttributeError) as e:
        print(f"Error during initial request: {e}")

def get_resume(link):
    user_agent = fake_useragent.UserAgent()
    
    try:
        response = requests.get(link, headers={'user-agent': user_agent.random})
        response.raise_for_status()  # Проверяем успешность запроса
        soup = BeautifulSoup(response.content, "lxml")
        
        title = soup.find(attrs={"class": "bloko-header-section-1"}).text if soup.find(attrs={"class": "bloko-header-section-1"}) else ''
        name = soup.find('a', attrs={'data-qa':'vacancy-company-name'}).text.replace('\xa0', ' ') if soup.find('a', attrs={'data-qa':'vacancy-company-name'}) else ''
        salary = soup.find('div', attrs={"data-qa": "vacancy-salary"}).text if soup.find('div', attrs={"data-qa": "vacancy-salary"}) else ''
        tags = [tag.text for tag in soup.find(attrs={"class": "vacancy-skill-list--COfJZoDl6Y8AwbMFAh5Z"}).find_all(attrs={"data-qa": "skills-element"})] if soup.find(attrs={"data-qa": "skills-element"}) else []
        experience = soup.find(attrs={"data-qa": "vacancy-experience"}).text if soup.find(attrs={"data-qa": "vacancy-experience"}) else ''
        busyness = soup.find(attrs={"data-qa": "vacancy-view-employment-mode"}).text if soup.find(attrs={"data-qa": "vacancy-view-employment-mode"}) else ''
       
        resume = {
            'title':title,
            'name':name,
            'tags':tags,
            'salary':salary,
            'experience':experience,
            'busyness':busyness,
        }
        return resume
    except (requests.RequestException, AttributeError) as e:
        print(f'Error fetching resume from {link}: {e}')
        return None

if __name__ == "__main__": 
    data = []
    keyword = "python"
    #education_filters = ["not_required_or_not_specified", "higher", "special_secondary"]
    education_filters = ["higher"]
    salary = 20000
    #part_time_filters = ["employment_part", "from_four_to_six_hours_in_a_day", "start_after_sixteen", "employment_project", "only_saturday_and_sunday"]
    part_time_filters = ["employment_part"]
    #experience = "between3And6"
    for link in get_links(keyword, education_filters, salary, part_time_filters):
        vacancy = get_resume(link)
        if vacancy:
            data.append(vacancy)
            time.sleep(0.5)  # Добавляем задержку между запросами, чтобы не нагружать сервер
            with open('vacancy.json', 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
