from operator import le
import requests
import time
import asyncio
from sqlalchemy import insert
from db import engine, get_item, items

# status codes
# 0 - Закончен
# 1 - Продолжается
# 4 - Анонс


async def add_data_in_db(data):

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


async def get_characters_date(id, headers):
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


async def get_title_info(link, headers):
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
            dates = await get_characters_date(branch_id, headers)
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


async def get_titles(link, headers):
    """Get all titles"""
    request = requests.get(link, headers=headers)
    if request.status_code == 200:
        content = request.json()['content']
        if len(content) > 0:
            for item in content:
                
                id = item['id']

                if await get_item(id) == None and id != None:

                    link = item['dir']
                    print(link)
                    en_name = item['en_name']
                    ru_name = item['rus_name']
                    year = item['issue_year']

                    info = await get_title_info(link, headers)

                    info['id'] = id
                    info['link'] = link
                    info['en_name'] = en_name
                    info['ru_name'] = ru_name
                    info['year'] = year

                    await add_data_in_db(info)




def get_count_page(link, headers):
    """Get the number of pages"""
    request = requests.get(link, headers=headers)
    if request.status_code == 200:
        content = request.json()['props']
        count = content['total_pages']
        return count


async def parsing_content(age_limit):
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
        asyncio.create_task(get_titles(link, headers))
        print(f'TASK <{page}> - started')
        page += 1

        if page % 10 == 0:
            await asyncio.sleep(10)


async def main():

    # parsing 18+
    # await parsing_content('age_limit=2&')

    # parsing all
    await parsing_content('')


asyncio.run(main())