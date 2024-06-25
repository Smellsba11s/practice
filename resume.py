import requests
from bs4 import BeautifulSoup
import fake_useragent
import json
import time

def get_links(keyword):
    user_agent = fake_useragent.UserAgent()
    url = f'https://hh.ru/search/resume?text={keyword}&area=1&isDefaultArea=true&exp_period=all_time&logic=normal&pos=full_text&page=0'
    
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
            url = f'https://hh.ru/search/resume?text={keyword}&area=1&isDefaultArea=true&exp_period=all_time&logic=normal&pos=full_text&page={page}'
            response = requests.get(url, headers={'user-agent': user_agent.random})
            response.raise_for_status()  
            
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
    for link in get_links('python'): # чисто условность, пользователь пишет что-то вместо python
        resume = get_resume(link)
        if resume:
            data.append(resume)
            time.sleep(0.5) 
            with open('data.json', 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
