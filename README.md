# Practice Project

Это проект для работы с вакансиями и резюме, а также Telegram бот для их обработки.

## Структура проекта



```
project/
│
├── backend/
│ ├── resume.py
│ ├── vacancy.py
│ ├── vacancy_average.py
│ 
├── bot/
│ ├── config.py
│ ├── run.py
│ ├── app/
│ │ ├── handlers.py
│ │ ├── bd_resume/(тут находится бд)
│ │ ├── bd_vacancy/(тут находится бд)
│ │ ├── keyboard.py
│ ├── requirements.txt
│ └── Dockerfile
│
└── docker-compose.yml
```


## Установка

Для быстрой установки вы можете использовать Docker Compose,
Вот пошаговая инструкция:
```
1) Установите Docker Compose Dekstop
2) Вбейте токен тг бота в config.py
3) В корневой папке проекта вызовите командную строку(сверху есть поиск по директории, там нужно написать cmd)
4) Впишите команду docker-compose up --build
5) Бот работает, пишите команду /start
```

## Описание файлов
# Backend
resume.py: Скрипт для работы с резюме. <br>
vacancy.py: Скрипт для работы с вакансиями. <br>
vacancy_average.py: Скрипт для расчета средних данных по вакансиям. <br>
# Bot
config.py: Конфигурационный файл для бота. <br>
run.py: Основной скрипт для запуска бота. <br>
app/handlers.py: Обработчики команд и сообщений. <br>
app/keyboard.py: Определение клавиатуры для бота. <br>
