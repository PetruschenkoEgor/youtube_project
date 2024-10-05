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

    cur.execute(f'DROP DATABASE IF EXISTS {database_name}')
    cur.execute(f'CREATE DATABASE {database_name}')

    cur.close()
    conn.close()

    conn = psycopg2.connect(dbname=database_name, **params)
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS channels (
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
            CREATE TABLE IF NOT EXISTS videos (
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
    conn = psycopg2.connect(dbname=database, **params)

    with conn.cursor() as cur:
        for channel in data:
            channel_data = channel['channel']['snippet']
            channel_stats = channel['channel']['statistics']
            cur.execute("""
                INSERT INTO channels (title, views, subscribers, videos, channel_url)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING channel_id
                """,
                (channel_data['title'], channel_stats['viewCount'], channel_stats['subscriberCount'],
                 channel_stats['videoCount'], f"https://www.youtube.com/channel/{channel['channel']['id']}")
            )
        channel_id = cur.fetchone()[0]
        videos_data = channel['videos']
        for video in videos_data:
            video_data = video['snippet']
            cur.execute("""
                INSERT INTO videos (channel_id, title, publish_date, video_url)
                VALUES (%s, %s, %s, %s)
                """,
                (channel_id, video_data['title'], videos_data['publishedAt'],
                 f"https://www.youtube.com/watch?v={video['id']['videoId']}")
            )

    conn.commit()
    conn.close()
