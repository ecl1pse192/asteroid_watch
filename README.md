# NEO Observer

Информационно-аналитическая система мониторинга потенциально опасных астероидов на основе данных NASA. Сервис помогает астрономам-любителям отслеживать небесные тела, сближающиеся с Землей.

**Ссылка на рабочий проект:** 

## Технологии
* **Python 3.13**
* **Django 5.2**
* **NASA NeoWs API**
* **Bootstrap 5**
* **Chart.js**

## Скриншоты 
*(Раздел находится в разработке. Скриншоты интерфейса будут добавлены 13.01)*

![Главная страница](static/img/screenshot_main_placeholder.png)
*Список астероидов с подсветкой опасных объектов*

![Личный кабинет](static/img/screenshot_dashboard_placeholder.png)
*Личный список наблюдения пользователя*

## Как запустить проект локально
1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/ecl1pse192/asteroid_watch.git
2. **Создайте и активируйте виртуальное окружение:**
    python -m venv venv
    # Для Windows:
    venv\Scripts\activate
    # Для Mac/Linux:
    source venv/bin/activate
3. **Установите зависимости:**
    pip install -r requirements.txt
4. **Настройте переменные окружения:**
    Создайте файл .env в корне проекта (рядом с manage.py) и добавьте:
    NASA_API_KEY=DEMO_KEY
5. **Выполните миграции:**
    python manage.py migrate
6. **Загрузите данные**
    Команда скачает актуальные данные с серверов NASA:
    python manage.py load_nasa
7. **Запустите сервер:**
    python manage.py runserver