import requests
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from constants import VK_TOKEN, API_WEATHER
from parsing import load_table, download_table
from vk_api.upload import VkUpload
import pickle
import os.path
import re
from sql import DatabaseFunction
import datetime
from COVID_parsing import draw_stat_rus_ten, get_today

name_days_week = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота"]
comands_days_week = ["бот понедельник", "бот вторник", "бот среда", "бот четверг", "бот пятница", "бот суббота"]



def num_week():
    now = datetime.datetime.now()
    now_week = now.isocalendar()[1]
    start_week = datetime.date(2022, 2, 9).isocalendar()[1]
    return now_week - start_week + 1


def get_weather():
    response = requests.get("http://api.openweathermap.org/data/2.5/weather?q=moscow&lang=ru&units=metric&appid={}&units=metric".format(API_WEATHER))
    info = response.json()
    return info


class Bot(object):
    def __init__(self):
        self.table = None
        self.session = vk_api.VkApi(token=VK_TOKEN)
        self.vk = self.session.get_api()
        self.db = DatabaseFunction()
        self.upload = VkUpload(self.vk)

        if os.path.exists('table.pickle'):
            self.load_table()
        else:
            download_table()

    def upload_photo(self, photo):
        response = self.upload.photo_messages(photo)[0]

        owner_id = response['owner_id']
        photo_id = response['id']
        access_key = response['access_key']

        return owner_id, photo_id, access_key

    def load_table(self):
        with open('table.pickle', 'rb') as f:
            self.table = pickle.load(f)

    def save_user(self, vk_id, group):
        self.db.save_user(vk_id, group)
        self.vk.messages.send(user_id=vk_id,
                              random_id=get_random_id(),
                              message='Я запомнил, что ты из группы ' + group)

    def send_chat_error(self, vk_id):
        self.vk.messages.send(user_id=vk_id,
                              random_id=get_random_id(),
                              message='Неизвестная команда')

    def show_keyboard(self, vk_id):
        kb = VkKeyboard(one_time=True)
        kb.add_button('на сегодня', color=VkKeyboardColor.NEGATIVE)
        kb.add_button('на завтра', color=VkKeyboardColor.POSITIVE)
        kb.add_line()
        kb.add_button('на эту неделю', color=VkKeyboardColor.PRIMARY)
        kb.add_button('на следующую неделю', color=VkKeyboardColor.PRIMARY)
        kb.add_line()
        kb.add_button('какая неделя?', color=VkKeyboardColor.SECONDARY)
        kb.add_button('какая группа?', color=VkKeyboardColor.SECONDARY)

        self.vk.messages.send(
            user_id=vk_id,
            random_id=get_random_id(),
            keyboard=kb.get_keyboard(),
            message='Показать расписание …'
        )

    def show_num_week(self, vk_id):
        self.vk.messages.send(user_id=vk_id,
                              random_id=get_random_id(),
                              message='Идет {} неделя'.format(num_week()))

    def show_group(self, vk_id):
        self.vk.messages.send(user_id=vk_id,
                              random_id=get_random_id(),
                              message='Показываю расписание группы {}'.format(self.db.get_group(vk_id)))

    def get_day(self, day, num, group):
        res = []
        table = self.table[group]
        for i in range(day * 12, day * 12 + 12):
            if (i % 2) != (num % 2):
                res.append(table[i])
        otv = ''
        for i in range(len(res) - 1):
            otv += '{}) {} \n'.format(str(i + 1), res[i])
        otv += '{}) {} '.format(str(6), res[-1])
        return otv

    def show_today(self, vk_id, group):
        day = datetime.datetime.now().weekday()
        if day != 6:
            msg = self.get_day(day, num_week(), group)
        else:
            msg = "Пар нет"
        self.vk.messages.send(user_id=vk_id,
                              random_id=get_random_id(),
                              message=msg)

    def show_tomorrow(self, vk_id, group):
        day = (datetime.datetime.now().weekday() + 1) % 7
        if day != 6:
            msg = self.get_day(day, num_week() + (datetime.datetime.now().weekday() + 1) // 7, group)
        else:
            msg = "Пар нет"
        self.vk.messages.send(user_id=vk_id,
                              random_id=get_random_id(),
                              message=msg)

    def show_this_week(self, vk_id, group):
        msg = ''
        for i in range(6):
            msg += '\n' + name_days_week[i] + '\n'
            msg += self.get_day(i, num_week(), group)
            msg += '\n' + '_______________________'
        self.vk.messages.send(user_id=vk_id,
                              random_id=get_random_id(),
                              message=msg)

    def show_next_week(self, vk_id, group):
        msg = ''
        for i in range(6):
            msg += '\n' + name_days_week[i] + '\n'
            msg += self.get_day(i, num_week() + 1, group)
            msg += '\n' + '_______________________'
        self.vk.messages.send(user_id=vk_id,
                              random_id=get_random_id(),
                              message=msg)

    def show_user_day(self, vk_id, day, group):
        msg = ''
        msg += self.get_day(day, 1, group) + '\n'
        msg += self.get_day(day, 2, group)
        self.vk.messages.send(user_id=vk_id,
                              random_id=get_random_id(),
                              message=msg)

    def show_group_keyboard(self, vk_id, group):
        kb = VkKeyboard(one_time=True)
        kb.add_button('на сегодня {}'.format(group), color=VkKeyboardColor.NEGATIVE)
        kb.add_button('на завтра {}'.format(group), color=VkKeyboardColor.POSITIVE)
        kb.add_line()
        kb.add_button('на эту неделю {}'.format(group), color=VkKeyboardColor.PRIMARY)
        kb.add_button('на следующую неделю {}'.format(group), color=VkKeyboardColor.PRIMARY)
        kb.add_line()
        kb.add_button('какая неделя?', color=VkKeyboardColor.SECONDARY)
        kb.add_button('какая группа?', color=VkKeyboardColor.SECONDARY)

        self.vk.messages.send(
            user_id=vk_id,
            random_id=get_random_id(),
            keyboard=kb.get_keyboard(),
            message='Показать расписание …'
        )

    def show_weather(self, vk_id):
        response = get_weather()
        msg = 'Погода в Москве ' + response['weather'][0]['description'] + "\n"
        msg += 'Температура: ' + str(response['main']['temp_min']) + '-' + str(response['main']['temp_max']) + "°C" + "\n"
        msg += 'Давление: ' + str(response['main']['pressure']*0.75) + 'мм рт. ст.'+ "Влажность " + str(response['main']['humidity']) + "%" + "\n"
        msg += 'Ветер: ' + str(response["wind"]['speed']) + 'м/с, ' + str(response["wind"]['deg']) + "°"
        self.vk.messages.send(user_id=vk_id,
                              random_id=get_random_id(),
                              message=msg)

    def show_covid(self, vk_id):
        msg = get_today()
        at = self.upload_photo(draw_stat_rus_ten())
        attachment = f'photo{at[0]}_{at[1]}_{at[2]}'
        self.vk.messages.send(
            random_id=get_random_id(),
            peer_id=vk_id,
            attachment=attachment,
            message=msg
        )

    def run(self):
        poll = VkLongPoll(self.session)
        for event in poll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.text:
                if len(re.findall(r'^\w+-\d{2}-\d{2}$', event.text)) == 1:
                    self.save_user(event.user_id, re.findall(r'^\w+-\d{2}-\d{2}$', event.text)[0])
                elif 'бот' == event.text.lower():
                    self.show_keyboard(event.user_id)
                elif 'какая неделя?' == event.text.lower():
                    self.show_num_week(event.user_id)
                elif 'какая группа?' == event.text.lower():
                    self.show_group(event.user_id)
                elif 'на сегодня' == event.text.lower():
                    self.show_today(event.user_id, self.db.get_group(event.user_id))
                elif 'на завтра' == event.text.lower():
                    self.show_tomorrow(event.user_id, self.db.get_group(event.user_id))
                elif 'на эту неделю' == event.text.lower():
                    self.show_this_week(event.user_id, self.db.get_group(event.user_id))
                elif 'на следующую неделю' == event.text.lower():
                    self.show_next_week(event.user_id, self.db.get_group(event.user_id))
                elif event.text.lower() in comands_days_week:
                    self.show_user_day(event.user_id, comands_days_week.index(event.text.lower()),
                                       self.db.get_group(event.user_id))
                elif len(re.findall(r'^бот \w+-\d{2}-\d{2}', event.text.lower())) == 1:
                    self.show_group_keyboard(event.user_id, re.findall(r'\w+-\d{2}-\d{2}', event.text)[0])
                elif len(re.findall(r'^на сегодня \w+-\d{2}-\d{2}', event.text.lower())) == 1:
                    self.show_today(event.user_id, re.findall(r'\w+-\d{2}-\d{2}', event.text)[0])
                elif len(re.findall(r'^на завтра \w+-\d{2}-\d{2}', event.text.lower())) == 1:
                    self.show_tomorrow(event.user_id, re.findall(r'\w+-\d{2}-\d{2}', event.text)[0])
                elif len(re.findall(r'^на эту неделю \w+-\d{2}-\d{2}', event.text.lower())) == 1:
                    self.show_this_week(event.user_id, re.findall(r'\w+-\d{2}-\d{2}', event.text)[0])
                elif len(re.findall(r'^на следующую неделю \w+-\d{2}-\d{2}', event.text.lower())) == 1:
                    self.show_next_week(event.user_id, re.findall(r'\w+-\d{2}-\d{2}', event.text)[0])
                elif len(re.findall(r'^бот (?:понедельник|втоник|среда|четверг|пятница|суббота) \w+-\d{2}-\d{2}$',
                                    event.text.lower())) == 1:
                    self.show_user_day(event.user_id,
                                       name_days_week.index(
                                           re.findall(r'(?:понедельник|втоник|среда|четверг|пятница|суббота)',
                                                      event.text)[0]),
                                       re.findall(r'\w+-\d{2}-\d{2}', event.text)[0])
                elif 'погода' == event.text.lower():
                    self.show_weather(event.user_id)
                elif 'корона' == event.text.lower():
                    self.show_covid(event.user_id)


if __name__ == '__main__':
    get_weather()
    bot = Bot()
    bot.run()
