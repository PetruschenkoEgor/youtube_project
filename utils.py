from typing import Any
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


def create_database(database: str, params: dict) -> None:
    """ Создание базы данных и таблиц для сохранения данных о каналах и видео """


def save_data_to_database(data: list[dict[str, Any]], database: str, params: dict) -> None:
    """ Сохранение данных о каналах и видео в базу данных """
