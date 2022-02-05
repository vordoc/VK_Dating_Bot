import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_functions import search_users, get_photo, sort_likes, json_create
from interaction_with_db import engine, Session, write_msg, register_user, add_user, add_user_photos, add_to_black_list, \
    check_db_user, check_db_black, check_db_favorites, check_db_master, delete_db_blacklist, delete_db_favorites
from settings import group_token

vk = vk_api.VkApi(token=group_token)
longpoll = VkLongPoll(vk)

session = Session()
connection = engine.connect()


def bot_loop():
    for this_event in longpoll.listen():
        if this_event.type == VkEventType.MESSAGE_NEW:
            if this_event.to_me:
                message_text = this_event.text
                return message_text, this_event.user_id


def bot_menu(id_num):
    write_msg(id_num,
              f"Вас приветствует vkinder, чат-бот для знакомств!\n"
              f"\nВпервые здесь? - зарегистрируйтесь!\n"
              f"Для регистрации отправь мне сообщение - старт\n"
              f"Уже зарегистрированы? - начинайте поиск!\n"
              f"\nДля поиска отправь мне сообщение в формате:\n кого ищем (мужчина или женщина), возраст (от и до),"
              f"\nзамужем/женат - m, незамужем/холост - s, город проживания"
              f"\nПРИМЕР: \nженщина 20-30 m Москва  \n-ИЛИ-  "
              f"\nмужчина 35-45 s Сочи\n\n"
              f"Для перехода в избранное отправь мне сообщение - 2\n"
              f"Для перехода в черный список отправь мне - 0\n")


def show_info():
    write_msg(user_id, f'Это была последняя анкета'
                       f'Перейти в избранное - 2'
                       f'Перейти в черный список - 0'
                       f'Поиск - девушка 30-45 Москва  -ИЛИ-  парень 25-55 Сочи'
                       f'Меню бота - vkinder')


def new_user_registration(id_num):
    write_msg(id_num, 'Поздравляю! Вы зарегистрированы!')
    write_msg(id_num,
              f"vkinder - для активации бота\n")
    register_user(id_num)


def go_to_favorites(ids):
    all_users = check_db_favorites(ids)
    write_msg(ids, f'Избранные анкеты:')
    for nums, users in enumerate(all_users):
        write_msg(ids, f'{users.first_name}, {users.second_name}, {users.link}')
        write_msg(ids, '1 - Удалить из избранного, 3 - Далее \n0 - Выход')
        msg_texts, user_ids = bot_loop()
        if msg_texts == '3':
            if nums >= len(all_users) - 1:
                write_msg(user_ids, f'Это была последняя анкета.\n'
                                    f'vkinder - вернуться в меню\n')

        elif msg_texts == '1':
            delete_db_favorites(users.vk_id)
            write_msg(user_ids, f'Анкета успешно удалена.')
            if nums >= len(all_users) - 1:
                write_msg(user_ids, f'Это была последняя анкета.\n'
                                    f'vkinder - вернуться в меню\n')
        elif msg_texts.lower() == '0':
            write_msg(ids, 'vkinder - для активации бота.')
            break


def go_to_blacklist(ids):
    all_users = check_db_black(ids)
    write_msg(ids, f'Анкеты в черном списке:')
    for num, user in enumerate(all_users):
        write_msg(ids, f'{user.first_name}, {user.second_name}, {user.link}')
        write_msg(ids, '1 - Удалить из черного списка, 3 - Далее \n0 - Выход')
        msg_texts, user_ids = bot_loop()
        if msg_texts == '3':
            if num >= len(all_users) - 1:
                write_msg(user_ids, f'Это была последняя анкета.\n'
                                    f'vkinder - вернуться в меню\n')

        elif msg_texts == '1':
            print(user.id)
            delete_db_blacklist(user.vk_id)
            write_msg(user_ids, f'Анкета успешно удалена')
            if num >= len(all_users) - 1:
                write_msg(user_ids, f'Это была последняя анкета.\n'
                                    f'vkinder - вернуться в меню\n')
        elif msg_texts.lower() == '0':
            write_msg(ids, 'vkinder - для активации бота.')
            break


def main():
    while True:
        msg_text, user_id = bot_loop()
        if msg_text == "vkinder":
            bot_menu(user_id)
            msg_text, user_id = bot_loop()

            if msg_text.lower() == 'старт':
                new_user_registration(user_id)

            elif len(msg_text) > 1:
                sex = 0
                relation = 0
                if 'женщина' in msg_text.lower():
                    sex = 1
                elif 'мужчина' in msg_text.lower():
                    sex = 2
                age_from = int(msg_text[8:10])
                age_to = int(msg_text[11:14])
                city = msg_text[16:len(msg_text)].lower()
                if 's' in msg_text.lower():
                    relation = 1
                elif 'm' in msg_text.lower():
                    relation = 4

                result = search_users(sex, int(age_from), int(age_to), city, relation)
                # print(result)
                json_create(result)
                current_user_id = check_db_master(user_id)

                for i in range(len(result)):
                    dating_user, blocked_user = check_db_user(result[i][3])

                    user_photo = get_photo(result[i][3])
                    if user_photo == 'нет доступа к фото' or dating_user is not None or blocked_user is not None:
                        continue
                    sorted_user_photo = sort_likes(user_photo)

                    write_msg(user_id, f'\n{result[i][0]}  {result[i][1]}  {result[i][2]}', )
                    try:
                        write_msg(user_id, f'фото:',
                                  attachment=','.join
                                  ([sorted_user_photo[-1][1], sorted_user_photo[-2][1],
                                    sorted_user_photo[-3][1]]))
                    except IndexError:
                        for photo in range(len(sorted_user_photo)):
                            write_msg(user_id, f'фото:',
                                      attachment=sorted_user_photo[photo][1])

                    write_msg(user_id, '1 - Добавить, 2 - Заблокировать, 3 - Далее, \n0 - выход из поиска')
                    msg_text, user_id = bot_loop()
                    if msg_text == '3':
                        if i >= len(result) - 1:
                            show_info()

                    elif msg_text == '1':
                        if i >= len(result) - 1:
                            show_info()
                            break

                        try:
                            add_user(user_id, result[i][3], result[i][1],
                                     result[i][0], city, result[i][2], current_user_id.id)
                            add_user_photos(user_id, sorted_user_photo[0][1],
                                            sorted_user_photo[0][0], current_user_id.id)
                        except AttributeError:
                            write_msg(user_id, 'Вы не зарегистрировались!\n Введите vkinder для перезапуска!')
                            break

                    elif msg_text == '2':
                        if i >= len(result) - 1:
                            show_info()
                        add_to_black_list(user_id, result[i][3], result[i][1],
                                          result[i][0], city, result[i][2],
                                          sorted_user_photo[0][1],
                                          sorted_user_photo[0][0], current_user_id.id)
                    elif msg_text.lower() == '0':
                        write_msg(user_id, 'Введите vkinder для активации бота')
                        break

            elif msg_text == '2':
                go_to_favorites(user_id)

            elif msg_text == '0':
                go_to_blacklist(user_id)


if __name__ == '__main__':
    main()


