import requests
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from constants import VK_TOKEN, API_WEATHER
from vk_api.upload import VkUpload
import re
from sql import DatabaseFunction
import datetime
from convector import pressure, direction, type_wind, translate_weather
from COVID_parsing import draw_stat_rus_ten, get_today, get_area
import PIL.Image as Image
from datetime import date, timedelta
name_days_week = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота"]
comands_days_week = ["бот понедельник", "бот вторник", "бот среда", "бот четверг", "бот пятница", "бот суббота"]


def getst_index(info):
    patt = re.compile(f'09:00:00')
    arr = info['list']
    for indx in range(len(arr)):
        if re.search(patt, arr[indx]['dt_txt']):
            return indx


def five_day_wth(url=None):
    if url is None: url = "http://api.openweathermap.org/data/2.5/forecast?q=Moscow&appid=60c72ae4a0e1d6c84d837093e3b25a36&units=metric"
    response = requests.get(url)
    info = response.json()
    return info


def getf_weather(info):
    pr = pressure(info['main']['pressure'])
    dir = direction(info['wind']['deg'])
    typ = type_wind(info['wind']['speed'])
    weather = translate_weather(info['weather'][0]['main'])
    msg = f"{weather}, темпиратура: {info['main']['temp_min']} - {info['main']['temp_max']}°C\n"
    msg += f"Давление: {pr} мм.рт.ст., влажность: {info['main']['humidity']}%\n"
    msg += f"Ветер: {typ}, {info['wind']['speed']}м/с, {dir}"
    return msg


def num_week():
    now = datetime.datetime.now()
    now_week = now.isocalendar()[1]
    start_week = datetime.date(2022, 2, 9).isocalendar()[1]
    return now_week - start_week + 1


def get_weather():
    response = requests.get("http://api.openweathermap.org/data/2.5/weather?q=moscow&lang=ru&units=metric&appid={}&units=metric".format(API_WEATHER))
    info = response.json()
    return info


def current_weather(url=None):
    if url is None: url = f"http://api.openweathermap.org/data/2.5/weather?q=Moscow&appid=60c72ae4a0e1d6c84d837093e3b25a36&units=metric"
    response = requests.get(url)
    info = response.json()
    return info


class Bot(object):
    def __init__(self):
        self.table = None
        self.session = vk_api.VkApi(token=VK_TOKEN)
        self.vk = self.session.get_api()
        self.db = DatabaseFunction()
        self.upload = VkUpload(self.vk)

    def upload_photo(self, photo):
        response = self.upload.photo_messages(photo)[0]

        owner_id = response['owner_id']
        photo_id = response['id']
        access_key = response['access_key']

        return owner_id, photo_id, access_key

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
        table = self.db.get_table_group(group)
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
        msg += self.get_day(day, 1, group)
        msg += '\n' + '_______________________' + '\n'
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

    def show_reg_covid(self, vk_id, reg):
        reg = ' '.join(reg.split(' ')[1:])
        msg = get_area(reg)
        self.vk.messages.send(
            random_id=get_random_id(),
            peer_id=vk_id,
            message=msg
        )

    def show_teachers(self, vk_id, name):
        name = ' '.join(name.split(' ')[1:])
        teachers = self.db.get_teachers(name)
        if len(teachers) == 1:
            kb = VkKeyboard(one_time=True)
            kb.add_button('на сегодня {}'.format(teachers[0]), color=VkKeyboardColor.NEGATIVE)
            kb.add_button('на завтра {}'.format(teachers[0]), color=VkKeyboardColor.POSITIVE)
            kb.add_line()
            kb.add_button('на эту неделю {}'.format(teachers[0]), color=VkKeyboardColor.PRIMARY)
            kb.add_button('на следующую неделю {}'.format(teachers[0]), color=VkKeyboardColor.PRIMARY)
            self.vk.messages.send(
                user_id=vk_id,
                random_id=get_random_id(),
                keyboard=kb.get_keyboard(),
                message='Показать расписание …'
            )
        elif len(teachers) > 1:
            kb = VkKeyboard(one_time=True)
            for i in range(len(teachers)):
                kb.add_button(f'Найти {teachers[i]}', color=VkKeyboardColor.PRIMARY)
                if (i+1) % 4 == 0:
                    kb.add_line()
            self.vk.messages.send(
                user_id=vk_id,
                random_id=get_random_id(),
                keyboard=kb.get_keyboard(),
                message='Показать расписание …'
            )
        else:
            self.vk.messages.send(
                random_id=get_random_id(),
                peer_id=vk_id,
                message="нет такого преподавателя"
            )

    def show_teacher(self,user_id, name):
        name = ' '.join(name.split(' ')[1:])
        if self.db.get_table_teacher(name) is not None:
            kb = VkKeyboard(one_time=True)
            kb.add_button('на сегодня {}'.format(name), color=VkKeyboardColor.NEGATIVE)
            kb.add_button('на завтра {}'.format(name), color=VkKeyboardColor.POSITIVE)
            kb.add_line()
            kb.add_button('на эту неделю {}'.format(name), color=VkKeyboardColor.PRIMARY)
            kb.add_button('на следующую неделю {}'.format(name), color=VkKeyboardColor.PRIMARY)
            self.vk.messages.send(
                user_id=user_id,
                random_id=get_random_id(),
                keyboard=kb.get_keyboard(),
                message='Показать расписание …'
            )
        else:
            self.vk.messages.send(
                user_id=user_id,
                random_id=get_random_id(),
                message='нет такого преподавателя'
            )

    def get_day_teacher(self, day, num, name):
        res = []
        table = self.db.get_table_teacher(name)
        for i in range(day * 12, day * 12 + 12):
            if (i % 2) != (num % 2):
                res.append(table[i])
        otv = ''
        for i in range(len(res) - 1):
            otv += '{}) {} \n'.format(str(i + 1), res[i])
        otv += '{}) {} '.format(str(6), res[-1])
        return otv

    def show_today_teacher(self, user_id, teacher):
        name = ' '.join(teacher.split(' ')[2:])
        day = datetime.datetime.now().weekday()
        if day != 6:
            msg = self.get_day_teacher(day, num_week(), name)
        else:
            msg = "Пар нет"
        self.vk.messages.send(user_id=user_id,
                              random_id=get_random_id(),
                              message=msg)

    def show_tomorrow_teacher(self, user_id, teacher):
        name = ' '.join(teacher.split(' ')[2:])
        day = (datetime.datetime.now().weekday() + 1) % 7
        if day != 6:
            msg = self.get_day_teacher(day, num_week() + (datetime.datetime.now().weekday() + 1) // 7, name)
        else:
            msg = "Пар нет"
        self.vk.messages.send(user_id=user_id,
                              random_id=get_random_id(),
                              message=msg)

    def show_this_week_teacher(self, user_id, teacher):
        name = ' '.join(teacher.split(' ')[3:])
        msg = ''
        for i in range(6):
            msg += '\n' + name_days_week[i] + '\n'
            msg += self.get_day_teacher(i, num_week(), name)
            msg += '\n' + '_______________________'
        self.vk.messages.send(user_id=user_id,
                              random_id=get_random_id(),
                              message=msg)

    def show_next_week_teacher(self, user_id, teacher):
        name = ' '.join(teacher.split(' ')[3:])
        msg = ''
        for i in range(6):
            msg += '\n' + name_days_week[i] + '\n'
            msg += self.get_day_teacher(i, num_week() + 1, name)
            msg += '\n' + '_______________________'
        self.vk.messages.send(user_id=user_id,
                              random_id=get_random_id(),
                              message=msg)

    def show_weather_kb(self, user_id):
        self.kb_weather = VkKeyboard(one_time=True)
        self.kb_weather.add_button("сейчас", color=VkKeyboardColor.PRIMARY)
        self.kb_weather.add_button("сегодня", color=VkKeyboardColor.POSITIVE)
        self.kb_weather.add_button("завтра", color=VkKeyboardColor.POSITIVE)
        self.kb_weather.add_line()
        self.kb_weather.add_button("на 5 дней", color=VkKeyboardColor.POSITIVE)

        self.vk.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            keyboard=self.kb_weather.get_keyboard(),
            message="Показать погоду в Москве"
        )

    def build_photo(self, info, indx):
        attachments = []
        images = []
        for i in indx:
            url = f"http://openweathermap.org/img/wn/{info['list'][i]['weather'][0]['icon']}@2x.png"
            images.append(requests.get(url, stream=True).raw)
        image = Image.new('RGBA', (100 * len(indx), 100))  # RGBA!!!
        for i in range(len(indx)):
            img = Image.open(images[i])
            image.paste(img, (100 * i, 0))
        image.save("full_imag.png")

        photo = self.upload.photo_messages(photos="full_imag.png")[0]
        attachments.append(f"photo{photo['owner_id']}_{photo['id']}")
        return attachments

    def show_weathre_day(self, uid, fl):
        if not fl:
            mday = 'сегодня'
        else:
            mday = 'завтра'
        self.vk.messages.send(
            user_id = uid,
            random_id = get_random_id(),
            message = f"Погода в Москве {mday}"
            )
        info = five_day_wth()
        st_indx = getst_index(info)
        if fl == 0:
            indx = [st_indx] + [st_indx+i+2 for i in range(3)]
        elif fl == 1:
            indx = [st_indx+8] + [st_indx+i+10 for i in range(3)]
        attachments = self.build_photo(info, indx)
        self.vk.messages.send(
            user_id = uid,
            attachment = ','.join(attachments),
            random_id = get_random_id(),
            )

        title = ["УТРО\n", "\nДЕНЬ\n", "\nВЕЧЕР\n", "\nНОЧЬ\n"]
        msg = ""
        for i in range(4):
            msg += f"/{info['list'][indx[i]]['main']['temp']}/"
        msg += "\n\n"
        for i in range(4):
            msg += title[i]
            msg += getf_weather(info['list'][indx[i]])
        self.vk.messages.send(
            user_id = uid,
            random_id = get_random_id(),
            message = msg
            )

    def show_weather_now(self, user_id):
        self.vk.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            message="Погода в Москве"
        )
        info = current_weather()
        attachments = []
        url = f"http://openweathermap.org/img/wn/{info['weather'][0]['icon']}@2x.png"
        imag = requests.get(url, stream=True)
        photo = self.upload.photo_messages(photos=imag.raw)[0]
        attachments.append(f"photo{photo['owner_id']}_{photo['id']}")

        msg = getf_weather(info)
        self.vk.messages.send(
            user_id=user_id,
            attachment=','.join(attachments),
            random_id=get_random_id(),
        )
        self.vk.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            message=msg
        )

    def show_weathre_fiveday(self, uid):
        sday = str(date.today().day) + "." + str(date.today().month)
        fday = date.today() + timedelta(days=4)
        fday = str(fday.day) + "." + str(fday.month)
        self.vk.messages.send(
            user_id = uid,
            random_id = get_random_id(),
            message = f"Погода в Москве c {sday} по {fday}"
            )
        info = five_day_wth()
        st_indx = getst_index(info)
        indx_day = [st_indx+i for i in range(0, 33, 8)]
        indx_night = [st_indx+i for i in range(2, 35, 8)]
        attachments = self.build_photo(info, indx_day)
        self.vk.messages.send(
            user_id = uid,
            attachment = ','.join(attachments),
            random_id = get_random_id(),
            )

        msg = ""
        for i in range(4):
            msg += f"/{info['list'][indx_day[i]]['main']['temp']}°/"
        msg += "День\n"
        for i in range(4):
            msg += f"/{info['list'][indx_night[i]]['main']['temp']}°/"
        msg += "Ночь"
        self.vk.messages.send(
            user_id = uid,
            random_id = get_random_id(),
            message = msg
            )

    def run(self):
        poll = VkLongPoll(self.session)
        for event in poll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.text:
                if len(re.findall(r'^\w+-\d{2}-\d{2}$', event.text)) == 1:
                    self.save_user(event.user_id, re.findall(r'^\w+-\d{2}-\d{2}$', event.text)[0])
                elif 'погода' == event.text.lower():
                    self.show_weather_kb(event.user_id)
                elif 'сейчас' == event.text.lower():
                    self.show_weather_now(event.user_id)
                elif 'сегодня' == event.text.lower():
                    self.show_weathre_day(event.user_id, 0)
                elif 'завтра' == event.text.lower():
                    self.show_weathre_day(event.user_id, 1)
                elif 'на 5 дней' == event.text.lower():
                    self.show_weathre_fiveday(event.user_id)
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
                elif len(re.findall(r'^бот (?:понедельник|вторник|среда|четверг|пятница|суббота) \w+-\d{2}-\d{2}$',
                                    event.text.lower())) == 1:
                    self.show_user_day(event.user_id,
                                       name_days_week.index(
                                           re.findall(r'(?:понедельник|вторник|среда|четверг|пятница|суббота)',
                                                      event.text)[0]),
                                       re.findall(r'\w+-\d{2}-\d{2}', event.text)[0])
                elif 'погода' == event.text.lower():
                    self.show_weather(event.user_id)
                elif 'корона' == event.text.lower():
                    self.show_covid(event.user_id)
                elif len(re.findall(r'^корона \w+', event.text.lower())) == 1:
                    self.show_reg_covid(event.user_id, event.text)
                elif len(re.findall(r'^найти \w+ \w.\w.', event.text.lower())) == 1:
                    self.show_teacher(event.user_id, event.text)
                elif len(re.findall(r'^найти \w+$', event.text.lower())) == 1:
                    self.show_teachers(event.user_id, event.text)
                elif len(re.findall(r'^на сегодня \w+ \w.\w.', event.text.lower())) == 1:
                    self.show_today_teacher(event.user_id, event.text)
                elif len(re.findall(r'^на завтра \w+ \w.\w.', event.text.lower())) == 1:
                    self.show_tomorrow_teacher(event.user_id, event.text)
                elif len(re.findall(r'^на эту неделю \w+ \w.\w.', event.text.lower())) == 1:
                    self.show_this_week_teacher(event.user_id, event.text)
                elif len(re.findall(r'^на следующую неделю \w+ \w.\w.', event.text.lower())) == 1:
                    self.show_next_week_teacher(event.user_id, event.text)


if __name__ == '__main__':
    get_weather()
    bot = Bot()
    bot.run()
