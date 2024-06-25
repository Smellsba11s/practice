import requests
from bs4 import BeautifulSoup
import fake_useragent
import json
import time

def get_links(keyword):
    user_agent = fake_useragent.UserAgent()
    url = f'https://hh.ru/search/vacancy?text={keyword}&area=1&page=1'
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
            url = f'https://hh.ru/search/vacancy?text={keyword}&area=1&page={page}'
            response = requests.get(url, headers={'user-agent': user_agent.random})
            response.raise_for_status()  
            
            soup = BeautifulSoup(response.content, 'lxml')
            for a in soup.find_all('a', attrs={'class':'bloko-link'}):
                href = a.attrs['href'].split('?')[0]
                if '/vacancy/' in href: yield href
        except (requests.RequestException, AttributeError) as e:
            print(f'Error during page {page} request: {e}')
        time.sleep(1)
def get_resume(link):
    user_agent = fake_useragent.UserAgent()
    
    try:
        response = requests.get(link, headers={'user-agent': user_agent.random})
        response.raise_for_status()  # Проверяем успешность запроса
        soup = BeautifulSoup(response.content, "lxml")
        
        title = soup.find(attrs={"class": "bloko-header-section-1"}).text if soup.find(attrs={"class": "bloko-header-section-1"}) else ''
        name = soup.find('a', attrs={'data-qa':'vacancy-company-name'}).text.replace('\xa0', ' ') if soup.find('a', attrs={'data-qa':'vacancy-company-name'}) else ''
        salary = soup.find(attrs={"data-qa": "vacancy-salary-compensation-type-net"}).text.replace('\xa0','') if soup.find(attrs={"data-qa": "vacancy-salary-compensation-type-net"}) else ''
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
    vacancy = []
    for link in get_links('python'): # чисто условность, пользователь пишет что-то вместо python
        resume = get_resume(link)
        if resume:
            vacancy.append(resume)
            time.sleep(0.5) 
            with open('vacancy.json', 'w', encoding='utf-8') as file:
                json.dump(vacancy, file, indent=4, ensure_ascii=False)
