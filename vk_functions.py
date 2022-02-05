import vk_api
import json
import datetime
from vk_api.longpoll import VkLongPoll
from settings import group_token, user_token, version
from vk_api.exceptions import ApiError
from interaction_with_db import engine, Session

vk = vk_api.VkApi(token=group_token)
longpoll = VkLongPoll(vk)
session = Session()
connection = engine.connect()


def search_users(sex, age_from, age_to, city, relation):
    all_persons = []
    profile_link = 'https://vk.com/id'
    vk_ = vk_api.VkApi(token=user_token)
    response = vk_.method('users.search',
                          {'sort': 1,
                           'sex': sex,
                           'status': 1,
                           'age_from': age_from,
                           'age_to': age_to,
                           'has_photo': 1,
                           'count': 25,
                           'online': 1,
                           'hometown': city,
                           'relationj': relation
                           })
    for element in response['items']:
        person = [
            element['first_name'],
            element['last_name'],
            profile_link + str(element['id']),
            element['id']
        ]
        all_persons.append(person)
    return all_persons


def get_photo(user_owner_id):
    vk_ = vk_api.VkApi(token=user_token)
    try:
        response = vk_.method('photos.get',
                              {
                                  'access_token': user_token,
                                  'v': version,
                                  'owner_id': user_owner_id,
                                  'album_id': 'profile',
                                  'count': 10,
                                  'extended': 1,
                                  'photo_sizes': 1,
                              })
    except ApiError:
        return 'нет доступа к фото'
    users_photos = []
    for i in range(10):
        try:
            users_photos.append(
                [response['items'][i]['likes']['count'],
                 'photo' + str(response['items'][i]['owner_id']) + '_' + str(response['items'][i]['id'])])
        except IndexError:
            users_photos.append(['нет фото'])
    return users_photos


def sort_likes(photos):
    result = []
    for element in photos:
        if element != ['нет фото'] and photos != 'нет доступа к фото':
            result.append(element)
    return sorted(result)


def json_create(lst):
    today = datetime.date.today()
    today_str = f'{today.day}.{today.month}.{today.year}'
    res = {}
    res_list = []
    for num, info in enumerate(lst):
        res['data'] = today_str
        res['first_name'] = info[0]
        res['second_name'] = info[1]
        res['link'] = info[2]
        res['id'] = info[3]
        res_list.append(res.copy())

    with open("result.json", "a", encoding='UTF-8') as write_file:
        json.dump(res_list, write_file, ensure_ascii=False)

    print(f'Data successfully written in result.json')


