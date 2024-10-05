from typing import Any

import psycopg2
from googleapiclient.discovery import build


def get_youtube_data(api_key: str, channel_ids: list[str]) -> list[dict[str, Any]]:
    """ Получение данных о каналах и видео с помощью API YouTube. """
    youtube = build('youtube', 'v3', developerKey=api_key)

    data = []
    videos_data = []
    next_page_token = None
    for channel_id in channel_ids:
        # Получение информации о каналах
        channel_data = youtube.channels().list(part='snippet,statistics', id=channel_id).execute()

        while True:
            # Получение видео
            response = youtube.search().list(part='id,snippet', channelId=channel_id, type='video',
                                             order='date', maxResults=50, pageToken=next_page_token).execute()
            videos_data.extend(response['items'])

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

        data.append({
            'channel': channel_data['items'][0],
            'videos': videos_data
        })

    return data


def create_database(database_name: str, params: dict) -> None:
    """ Создание базы данных и таблиц для сохранения данных о каналах и видео """
    conn = psycopg2.connect(dbname='postgres', **params)
    # автоматическое сохранение при каждом sql запрос
    conn.autocommit = True
    cur = conn.cursor()

    # Обрабатываем исключение, если БД изначально не существует
    try:
        cur.execute(f'DROP DATABASE {database_name}')

    except Exception as e:
        print(f"Информация: {e}")

    finally:
        cur.execute(f'CREATE DATABASE {database_name}')

    cur.close()
    conn.close()

    conn = psycopg2.connect(dbname=database_name, **params)
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE channels (
                channel_id serial PRIMARY KEY,
                title varchar(255) NOT NULL,
                views integer,
                subscribers integer,
                videos integer,
                channel_url text
            )
        """)

    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE vedeos (
                video_id serial PRIMARY KEY,
                channel_id int REFERENCES channels(channel_id),
                title varchar NOT NULL,
                publish_date date,
                video_url text
            )
        """)

    conn.commit()
    conn.close()


def save_data_to_database(data: list[dict[str, Any]], database: str, params: dict) -> None:
    """ Сохранение данных о каналах и видео в базу данных """
