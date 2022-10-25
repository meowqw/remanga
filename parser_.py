import requests
import time
from threading import Thread
from sqlalchemy import insert, update
from db import engine, get_item, items
import time
import datetime
from bot import send_msg
# status codes
# 0 - Закончен
# 1 - Продолжается
# 4 - Анонс

tg_ids = ['678552606', '1655138958', '892464638']

def add_data_in_db(data):

    # add title in db    
    ins = insert(items).values(
        id = data['id'],
        link = data['link'],
        ru_name = data['ru_name'],
        en_name = data['en_name'],
        publisher = data['publisher'],
        year = data['year'],
        status = data['status'],
        count_chapters = data['count_chapters'],
        age = data['age'],
        date_first_character = data['date_first_character'],
        date_last_character = data['date_last_character']
    )
    conn = engine.connect()
    conn.execute(ins)


    print(data['id'], data['en_name'])
    
def send_logic(data, old_data):
    """SENDING NOTIFICATION LOGIC"""
    
    
    days_count = datetime.datetime.now() - old_data.created_on

    if data['date_last_character'] != None:

        date_last = datetime.datetime.strptime(data['date_last_character'], '%Y-%m-%dT%H:%M:%S.%f')
        days_last_character = datetime.datetime.now() - date_last
    else:
        days_last_character = None
    
    # 1 state (нет глав ИЛИ не менялся переводчик И с момента попадания в бд прошло 8 дней)
    if int(days_count.days) >= 8:
        if data['publisher'] == old_data.publisher or data['count_chapters'] == 0:
            
            for tg_id in tg_ids:
                send_msg(tg_id, 'https://remanga.org/manga/' + data['link'])
        
        # 3 state (был изменен переводчик И есть главы И прошло 8 дней)   
        elif days_last_character != None:
            if data['publisher'] != old_data.publisher and data['count_chapters'] > 0 and int(days_last_character.days) >= 8:
                
                for tg_id in tg_ids:
                    send_msg(tg_id, 'https://remanga.org/manga/' + data['link'])
            
                
    
    # 2 state (есть главы И с момента публикации последней прошло 3 месяца И статус = 1)
    if days_last_character != None:
        if int(days_last_character.days) > 90:
            if data['count_chapters'] > 0 and data['status'] == 1: 
                if days_last_character != None:
                    if int(days_last_character.days) > 90:
                        for tg_id in tg_ids:
                            send_msg(tg_id, 'https://remanga.org/manga/' + data['link'])
                            
            # 4 state (был изменен переводчик И есть главы И прошло 90 дней) 
            elif data['publisher'] != old_data.publisher and data['count_chapters'] > 0 and int(days_last_character.days) >= 90:
                
                for tg_id in tg_ids:
                    send_msg(tg_id, 'https://remanga.org/manga/' + data['link'])
                    
    
def update_data_in_db(data, old_data):
    
    # send notification
    send_logic(data, old_data)
    
            
    upd = update(items).where(items.c.id==data['id']).values(
        link = data['link'],
        ru_name = data['ru_name'],
        en_name = data['en_name'],
        publisher = data['publisher'],
        year = data['year'],
        status = data['status'],
        count_chapters = data['count_chapters'],
        age = data['age'],
        date_first_character = data['date_first_character'],
        date_last_character = data['date_last_character']
    )
    conn = engine.connect()
    conn.execute(upd)


def get_characters_date(id, headers):
    request = requests.get(
        f'https://api.remanga.org/api/titles/chapters/?branch_id={id}&ordering=-index&user_data=1&count=40&page=1',
        headers=headers)
    if request.status_code == 200:
        content = request.json()['content']
        last = content[0]['upload_date']

    request = requests.get(
        f'https://api.remanga.org/api/titles/chapters/?branch_id={id}&ordering=index&user_data=1&count=40&page=1',
        headers=headers)
    if request.status_code == 200:
        content = request.json()['content']
        first = content[0]['upload_date']

    return {'last': last, 'first': first}


def get_title_info(link, headers):
    """Get title info"""
    request = requests.get(f'https://api.remanga.org/api/titles/{link}',
                           headers=headers)

    if request.status_code == 200:
        
        content = request.json()['content']
        status = content['status']['id']
        count_chapters = content['count_chapters']
        age = content['age_limit']

        try:
            publisher = content['publishers'][0]['name']
        except Exception as e:
            publisher = None
        
        try:
            branch_id = content['branches'][0]['id']
        except Exception as e:
            branch_id = None

        # parsing date
        if int(count_chapters) > 0 and branch_id != None:
            dates = get_characters_date(branch_id, headers)
            date_last_character = dates['last']
            date_first_character = dates['first']
        else:
            date_last_character = None
            date_first_character = None

        return {
            'status': status,
            'count_chapters': count_chapters,
            'age': age,
            'date_last_character': date_last_character,
            'date_first_character': date_first_character,
            'publisher': publisher
        }


def get_titles(link, headers):
    """Get all titles"""
    request = requests.get(link, headers=headers)
    if request.status_code == 200:
        content = request.json()['content']
        if len(content) > 0:
            for item in content:
                
                id = item['id']
                
                if id != None:
                    item_data = get_item(id)
                    

                    link = item['dir']
                    print(link)
                    en_name = item['en_name']
                    ru_name = item['rus_name']
                    year = item['issue_year']

                    info = get_title_info(link, headers)

                    info['id'] = id
                    info['link'] = link
                    info['en_name'] = en_name
                    info['ru_name'] = ru_name
                    info['year'] = year

                    if item_data == None:

                        add_data_in_db(info)
                    else:
                        
                        # upd and sending notification
                        update_data_in_db(info, item_data)
                    




def get_count_page(link, headers):
    """Get the number of pages"""
    request = requests.get(link, headers=headers)
    if request.status_code == 200:
        content = request.json()['props']
        count = content['total_pages']
        return count


def parsing_content(age_limit):
    headers = {
        "accept":
        "*/*",
        "user-agent":
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"
    }

    # add token
    headers['authorization'] = 'bearer ip7k073j7WG16QSMKRVQ8QWx1giLee'

    page = 1
    start_link = f'https://api.remanga.org/api/search/catalog/?{age_limit}count=30&ordering=-chapter_date&page=1'
    count_page = get_count_page(start_link, headers)

    while page <= int(count_page):
        link = f'https://api.remanga.org/api/search/catalog/?{age_limit}count=30&ordering=-chapter_date&page={page}'
        print(link)
        Thread(target=get_titles, args=(link, headers)).start()
        print(f'TASK <{page}> - started')
        page += 1

        if page % 10 == 0:
            time.sleep(10)


def main():

    # parsing 18+
    parsing_content('age_limit=2&')

    # parsing all
    parsing_content('')

main()