# Сравниваем вакансии программистов

Скрипт выводит информацию по количеству вакансий и средней зп с двух сайтов [hh.ru](https://hh.ru) и [Super Job](https://superjob.ru).

### Как установить

1. Для запуска скрипта нужен токен(ключ) Super Job API. Создается [здесь](https://api.superjob.ru/).
Его надо поместить в файл ` .env `, находящийся в каталоге со скриптом. Токен записывается в файл следующим образом:
```
SUPER_JOB_API='oLEkSsK4QxxYuohok5Ff12sd1ASD2ASdlY8Moo3scqAn71'
```
2. Python3 должен быть уже установлен. 
Затем используйте `pip` (или `pip3`, есть конфликт с Python2) для установки зависимостей:
```
pip install -r requirements.txt
```

### Запуск

Скрипт запускается стандартным способом:

```
py main.py
```

### Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).
