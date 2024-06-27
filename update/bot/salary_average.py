import sqlite3
import re

def extract_numbers(salary_str):
    return [int(num.replace('\xa0', '')) for num in re.findall(r'\d[\d ]*\d', salary_str)]

def calculate_average(numbers):
    if len(numbers) == 0:
        return 0
    return sum(numbers) / len(numbers)

def calculate_average_salary(keyword):
    conn = sqlite3.connect('bd_vacancy/vacancy.db')
    cursor = conn.cursor()

    cursor.execute(f"SELECT salary FROM {keyword}")
    rows = cursor.fetchall()

    salaries = []

    for row in rows:
        salary_str = row[0]
        
        if "Не указана" in salary_str:
            continue
        
        numbers = extract_numbers(salary_str)
        
        if numbers:
            if len(numbers) == 2:
                average_salary = calculate_average(numbers)
                salaries.append(average_salary * 1000)
            elif len(numbers) == 1:
                salaries.append(numbers[0] * 1000)

    conn.close()

    if len(salaries) > 0:
        average_salary = sum(salaries) / len(salaries)
        return average_salary
    else:
        return 0
