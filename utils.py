import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

def get_week_from_date(date_str):
    """Возвращает номер недели по дате в формате YYYY-MM-DD."""
    date = datetime.strptime(date_str, "%Y-%m-%d")
    return date.isocalendar()[1]

def parse_data(url):
    """Парсит расписание с сайта по указанному URL."""
    response = requests.get(url)
    response.raise_for_status()  # Поднимет исключение при неудачном запросе

    soup = BeautifulSoup(response.text, 'html.parser')
    group_name = (
        soup.select_one('div.content > div.alert.alert-info p:nth-of-type(2) b')
        .get_text(strip=True) if soup.select_one('div.content > div.alert.alert-info p:nth-of-type(2) b') else "Unknown Group"
    )

    schedule_data = []
    is_even_week = get_week_from_date(re.search(r"date=(\d{4}-\d{1,2}-\d{1,2})", url).group(1)) % 2 == 1

    for day_schedule in soup.select('h3.day-heading + div'):
        subjects = []
        for subject in day_schedule.select('.class-line-item'):
            class_tail_selector = (
                '.class-tail.class-even-week' if is_even_week else '.class-tail.class-odd-week'
            )
            class_tails = subject.select(f"{class_tail_selector}, .class-tail.class-all-week")

            for class_tail in class_tails:
                # Извлекаем class-info и разделяем на тип занятия и имя преподавателя
                class_info_tag = class_tail.select_one('.class-info')
                class_type = class_info_tag.get_text(strip=True) if class_info_tag else ""
                teacher_name = ""

                if class_info_tag:
                    link_tag = class_info_tag.select_one('a')
                    if link_tag:
                        class_type = class_info_tag.contents[0].strip()  # Первый элемент — тип занятия
                        teacher_name = link_tag.get_text(strip=True)  # Имя преподавателя из ссылки

                class_pred = class_tail.select_one('.class-pred').get_text(strip=True) if class_tail.select_one('.class-pred') else ""
                class_aud = class_tail.select_one('.class-aud').get_text(strip=True) if class_tail.select_one('.class-aud') else ""
                class_group = class_tail.select_one('.class-info:nth-of-type(2)').get_text(strip=True) if class_tail.select_one('.class-info:nth-of-type(2)') else ""
                class_time = subject.select_one('.class-tails .class-time').get_text(strip=True) if subject.select_one('.class-tails .class-time') else ""

                # Проверка наличия тега span с фоном #94fff3, img и b внутри
                academy_it_tag = ""
                span_element = class_tail.select_one(".class-pred span[style*='background:#94fff3']")
                if span_element and span_element.find("img") and span_element.find("b"):
                    academy_it_tag = "Академия ИТ | "

                # Добавляем тег перед названием предмета, если проверка пройдена
                class_type = f"{academy_it_tag}{class_type}" if class_type.lower() != "свободно" else class_type

                if class_type.lower() != "свободно":
                    subjects.append({
                        "time": class_time,
                        "type": class_type,
                        "teacher": teacher_name,
                        "title": class_pred,
                        "room": class_aud,
                        "group": class_group,
                    })
        
        day_text = day_schedule.find_previous_sibling("h3").get_text(strip=True) if day_schedule.find_previous_sibling("h3") else "Unknown Day"
        schedule_data.append({
            "day": day_text,
            "subjects": subjects
        })

    return {"groupName": group_name, "scheduleData": schedule_data}


async def get_data(base_url):
    current_date = datetime.now().strftime("%Y-%m-%d")
    next_week_date = (datetime.now() + timedelta(weeks=1)).strftime("%Y-%m-%d")
    
    data1 = parse_data(f"{base_url}&date={current_date}")
    data2 = parse_data(f"{base_url}&date={next_week_date}")
    
    return {
        "data": [data1.get("scheduleData"), data2.get("scheduleData")],
        "groupName": data1.get("groupName")
    }


async def scrape_groups(url):
    print(url)
    """Парсит список курсов и групп с указанного URL."""
    response = requests.get(url)
    response.raise_for_status()  # Проверка на успешный запрос

    soup = BeautifulSoup(response.text, 'html.parser')

    # import codecs
    # fileObj = codecs.open(r"O:\Projects\Web\schedule_api\index.html", "r", "utf_8_sig" )
    # soup = BeautifulSoup(fileObj, 'html.parser')
    
    content_element = soup.select_one('div.content')
    kurs_list_element = content_element.select_one('ul.kurs-list')


    # Находим только верхние элементы курсов
    kurs_elements = kurs_list_element.select('li > ul')
    courses = []

    for kurs in kurs_elements:
        # Находим заголовок курса (предыдущий элемент перед списком групп)
        course_title = kurs.find_previous_sibling(text=True).strip()
        
        # Собираем все группы внутри текущего курса
        groups = [{
            "title": group.text, 
            "id": group['href'].split('=')[1] # получаем только id группы
        } for group in kurs.select('li a')]
        
        # Добавляем в результат курс и его группы
        courses.append({
            'course_title': course_title,
            'groups': groups
        })

    return courses