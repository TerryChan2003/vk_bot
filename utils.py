import math
from transliterate import translit
from vk_api.bot_longpoll import CHAT_START_ID
from vk_api.utils import get_random_id
from vk_api import VkApi
from vk_api.execute import VkFunction
from gtts.tts import gTTS
from random import choice
from vk_api.upload import VkUpload
import speech_recognition as sr
from pydub import AudioSegment
import wget
from pprint import pprint
import re
import json
import datetime
from module import *
from functools import wraps
import pymorphy2
morph = pymorphy2.MorphAnalyzer()

db = DB()

with open("config.json", "r") as f:
    data = json.load(f)

bug_priority = {
    1: "Низкий",
    2: "Средний",
    3: "Высокий",
    4: "Критический",
    5: "Уязвимость",
    6: "Предложение"
}

bug_status = {
    0: "Открыт",
    1: "В рассмотрении",
    2: "В работе",
    3: "Исправлен",
    4: "Закрыт",
    5: "Отклонен"
}

lvl_name = {
    0: "User",
    1: "Moderator",
    2: "Administrator",
    3: "Chief Administrator",
    4: "Special Administrator",
    5: "Developer"
}

sex_str = [
    "о",
    "а",
    ""
]

vk_platforms = {
    1: "&#128241; (m.vk.com)",
    2: "&#128241; (iPhone)",
    3: "&#128241; (iPad)",
    4: "&#128241; (Android)",
    5: "&#128241; (Windows Phone)",
    6: "&#128187; (Windows 10)",
    7: "&#128187; (vk.com)"
}

time_words = [
    morph.parse("секунда")[0],
    morph.parse("минута")[0],
    morph.parse("час")[0],
    morph.parse("день")[0],
    morph.parse("неделя")[0],
    morph.parse("месяц")[0],
    morph.parse("год")[0]
]

# Для обычных пользователей
help_list = ["""/help - Показать эту информацию
/rep - Написать сообщение разработчикам
/getadmin - Получить должности для руководителей конференции
/open - Показать клавиатуру
/clavs - Скрыть клавиатуру
/stat - Узнать свою должность
/info - Информация о боте
/admins - Список администраторов конференции
/say_rus - Озвучить текст на русском языке
/say_eng - Озвучить текст на английском языке
/get_warns - Список людей с предупреждениями
/refer_switch - Переключает упоминание для Вас Вкл/Выкл
/online - Выводит список пользователей с онлайном"""
             ]
# Для модераторов
help_list += [help_list[-1] + "\n" + """/kick - Исключить пользователя из конференции
/warn - Выдать предупреждение пользователю
/unwarn - Снять предупреждение пользователю
/whitelist - Выводит белый список"""]
# Для администраторов
help_list += [help_list[-1] + "\n" + """/ban - Заблокировать пользователя в конференции
/unban - Разблокировать пользователя в конференции
/title - Сменить название конференции
/refer - Упомянуть всем участникам конференции
/akick - Разрешить/запретить исключать при выходе
/blist - Просмотреть список заблокированных пользователей"""]
# Для создателей беседы
help_list += [help_list[-1] + "\n" + """/addadmin - Назначить пользователя на пост администратора
/deladmin - Снять пользователя с поста администратора
/chatid - Узнать ID данной конференции
/addgreeting - Создать приветствие
/delgreeting - Удалить приветствие
/greeting - Проверить приветствие
/warn_switch - Переключатель для разрешения команд предупреждений
/warn_kick_set - Используется для установления лимита предупреждений
/enable_check_group - Ограничение вступления по участникам в группе
/disable_check_group - Выключает ограничения по вступлению
/addwhite - Добавляет в белый список чтобы не проверяло по группе
/delwhite - Удаляет из белого списка и разрешает проверку по группе"""]
# Для спецадминистраторов
help_list += [help_list[-1] + "\n" + """/addblack - Добавить пользователя в черный спискок
/delblack - Убрать пользователя из черного списка
/checkblack - Просмотреть черный список
/addhelper - Назначить пользователя агентом поддержки
/delhelper - Снять пользователя с поста агента поддержки
/hstats - Проверить статистику агента поддержки
/hwarn - Выдать выговор агенту поддержки
/hunwarn - Снять выговор агенту поддержки
/stats - Узнать должность пользователя
/getinfo - Узнать информацию о чатах"""]
# Для разработчиков
help_list += [help_list[-1] + "\n" + """/get_commands - Узнать все включенные команды и их характеристики - В разработке для разработчиков
/get_command_code - Отображает содержимое кода команды - В разработке для разработчиков
/mute_report - Запретить пользователю писать сообщения в репорт
/unmute_report - Разрешить пользователю писать сообщения в репорт
/setrep - Обновить репорты агента - поддержки"""]

permissions = [[], [], [], [], [], []]
helper_permissions = []
requirements = {}
client_secret = data["client_secret"]
token = data["token"]
service_token = data["service_token"]
vk_s = VkApi(token=service_token).get_api()
secret_key = data["secret_key"]
groupid = data["group_id"]
devlist = data["devlist"]
speclist = data["speclist"]
devspeclist = devlist + speclist
pattern_user_id = r"\[id(\d+)\|[^\]]+\]|id(\d+)"
pattern_group_id = r"\[club(\d+)\|[^\]]+\]"
pattern_url = r"https?://m?\.?vk.com/(.+)"
pattern_text = r'"([^"]+)"'
pattern_duplicate = r"(.+)\1+"
pattern_symbols = r'[^0-9a-zA-Zа-яА-Я\s]+'
commands = {}
en_alphavet = [chr(ord("a") + i) for i in range(26)]
session = VkApi(token=token, api_version="5.100")
vk = session.get_api()
uploader = VkUpload(session)
vk_get_chat_members = lambda *x: VkFunction(
    args=('chat_id',),
    clean_args=('chat_id',),
    code='''return API.messages.getConversationMembers({"peer_id" : 2000000000+%(chat_id)s}).items@.member_id;''')(vk, *x)
vk_member_exists = lambda *x: bool(VkFunction(
    args=('chat_id', 'user_id'),
    clean_args=('chat_id', 'user_id'),
    code='''return parseInt(API.messages.getConversationMembers({"peer_id" : 2000000000+%(chat_id)s}).items@.member_id.indexOf(%(user_id)s) != -1);''')(vk, *x))
vk_member_can_kick = lambda *x: bool(VkFunction(
    args=('chat_id', 'user_id'),
    clean_args=('chat_id', 'user_id'),
    code='''var members = API.messages.getConversationMembers({"peer_id" : 2000000000+%(chat_id)s}).items;
    var member_ids = members@.member_id;
    var result = member_ids.indexOf(%(user_id)s);
    var member = members[result];
    if (member.can_kick){return 1;} else{return 0;}; ''')(vk, *x))
vk_send_multiple_messages = lambda *x: VkFunction(
    args=('kwargs', 'count'),
    clean_args=('kwargs', 'count'),
    code='''var i = 0;
    while (i < %(count)s) {
        API.messages.send(%(kwargs)s);
        i=i+1;
    }''')(vk, *x)


def get_role(from_id):
    if from_id not in devspeclist:
        helper = db.get_hstats(from_id)
        return f"Агент поддержки #{helper.id}"
    elif from_id in speclist:
        return f"Спецадминистратор #{speclist.index(from_id)+1}"
    else:
        return f"Разработчик #{devlist.index(from_id)+1}"


def users_get(user_id, fields="", **kwargs):
    try:
        return vk.users.get(user_ids=user_id, fields=fields, **kwargs)[0]
    except:
        ...


def group_words(words, word=".", length=4096, delimiter=""):
    r = []
    tmp = word
    for i in words:
        if len(tmp) + len(delimiter) + len(i) > length:
            r.append(tmp)
            tmp = word + delimiter + i
        else:
            tmp += delimiter + i
    if tmp:
        r.append(tmp)
    return r


def get_optimized_words(text):
    text = re.sub(pattern_symbols, '', text)
    r = re.sub(pattern_duplicate, r'\1', text)
    while r != text:
        text = r
        r = re.sub(pattern_duplicate, r'\1', text)
    words = list(set(translit(text, "ru").lower().split()))
    return words


def get_attachment_photo(photo):
    os.chdir("/root/server/tmp")
    max_p = 0
    for size in photo["sizes"]:
        if size["width"] * size["height"] > max_p:
            url = size["url"]
            max_p = size["width"] * size["height"]
    photo = wget.download(url)
    photo_js = uploader.photo_messages(photo)[0]
    os.remove(photo)
    return f"photo{photo_js['owner_id']}_{photo_js['id']}"


def groups_get(group_id, fields="", **kwargs):
    try:
        return vk.groups.getById(group_ids=group_id, fields=fields, **kwargs)[0]
    except:
        ...


def enable_for_helper(f):
    helper_permissions.append("/" + f.__name__)
    return f


def get_ref(peer_id, name_case=""):
    peer_id = int(peer_id)
    if peer_id > 0:
        x = users_get(peer_id, name_case=name_case)
        return f"@id{peer_id} ({x['first_name']} {x['last_name']})"
    else:
        peer_id = abs(peer_id)
        x = groups_get(peer_id)
        return f"@club{peer_id} ({x['name']})"


def parseArgs(args, fwd_messages, command, chat_id, reply_message=None, **kwargs):
    args = str(args) if args else None
    tmp = {
        "args": [],
        "user_ids": [],
        "text_args": [],
        "group_ids": []
    }
    if "text_args" in requirements[command]:
        for i in re.findall(pattern_text, args):
            tmp["text_args"].append(i)
        args = re.sub(pattern_text, "", args).strip()
    if "user_ids" in requirements[command] or "group_ids" in requirements[command]:
        user_ids = set()
        group_ids = set()
        if (fwd_messages or reply_message):
            if fwd_messages:
                for i in fwd_messages:
                    user_ids.add(i["from_id"])
            elif reply_message:
                user_ids.add(reply_message["from_id"])

        if args:
            for i in re.findall(pattern_url, args):
                r = vk.utils.resolveScreenName(screen_name=i)
                if r:
                    if r["type"] == "group":
                        user_ids.add(str(-r["object_id"]))
                        group_ids.add(str(r["object_id"]))
                    else:
                        user_ids.add(str(r["object_id"]))
            args = re.sub(pattern_url, "", args).strip()

        if args:
            for i in re.findall(pattern_group_id, args):
                user_ids.add(f"-{i}")
                group_ids.add(i)
            args = re.sub(pattern_group_id, "", args).strip()

        if args:
            for i in re.findall(pattern_user_id, args):
                for v in i:
                    if v:
                        user_ids.add(v)
            args = re.sub(pattern_user_id, "", args).strip()

        def filter_func(x): return not (x == "" or int(x) == 0 or (int(x) == 173243972 and command != "/enable_check_group"))
        tmp["group_ids"] = list(filter(filter_func, group_ids))
        tmp["user_ids"] = list(filter(filter_func, user_ids))
    if args:
        tmp["args"] = list(filter(lambda x: x.isdigit(), args.split()))
    if args and "user_ids" in requirements[command]:
        members = set(filter(lambda x: x > 0, vk_get_chat_members(chat_id)))
        r = Users.select().where(Users.user_id.in_(members))
        l = set()
        for i in r:
            l.add(i.user_id)
        try:
            for x in vk.users.get(user_ids=l ^ members, fields="sex, photo_200"):
                x["user_id"] = x["id"]
                del x["id"]
                print(Users(**x).save())
        except:
            ...
        for i in filter(lambda x: x not in tmp["args"], args.split()):
            r = Users.select().where(Users.user_id.in_(members), Users.last_name.startswith(i))
            c = r.count()
            if c == 0:
                sendmessage_chat(chat_id, f"Увы, ноль совпадений по фамилии {i}")
                raise Exception()
            elif c > 1:
                _s = '\n'.join([f'@id{x.user_id}' for x in r])
                sendmessage_chat(chat_id, f"Случилось совпадение фамилий {i}, выберите человека по упоминанию: {_s}")
                raise Exception()
            else:
                for i1 in r:
                    tmp["user_ids"].append(i1.user_id)
    return tmp


def enable_command(f, permission=0):
    cmd = "/" + f.__name__
    commands[cmd] = f
    for i in range(permission, 6):
        permissions[i].append(cmd)
    requirements[cmd] = f.__code__.co_varnames[:f.__code__.co_argcount] if not hasattr(f, "arguments") else f.arguments
    print("Команда {} была загружена".format(cmd))
    return f


def users_get_gen(user_id, fields=""):
    try:
        return vk.users.get(user_ids=user_id, fields=fields, name_case="Gen")[0]
    except:
        ...


def kick_chat_member(chat_id, member_id):
    try:
        vk.messages.removeChatUser(chat_id=chat_id, member_id=member_id)
        return True
    except:
        return False


def enable_command_with_permission(permission):
    return lambda x: enable_command(x, permission=permission)


def sendmessage(peer_id, message, **kwargs):
    vk.messages.send(peer_id=peer_id,
                     message=message, random_id=get_random_id(), **kwargs)


def sendmessage_chat(chat_id, message, **kwargs):
    vk.messages.send(chat_id=chat_id,
                     message=message, random_id=get_random_id(), **kwargs)


def exit_bot_chat(chat_id):
    vk.messages.removeChatUser(chat_id=chat_id, member_id=-groupid)


def get_format_time(stime, case="accs"):
    minutes, seconds = divmod(stime.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    days += stime.days
    weeks, days = divmod(days, 7)
    months, weeks = divmod(weeks, 4)
    years, months = divmod(months, 12)
    times = [seconds, minutes, hours, days, weeks, months, years]
    tmp = ["", "", "", "", "", "", ""]
    for k in range(len(tmp)):
        t = times[k]
        if t:
            tmp[k] = f"{t} {time_words[k].inflect({case}).make_agree_with_number(t).word}"
    tmp[-1] = tmp[-1].replace("годов", "лет")
    return ", ".join(list(filter(lambda x: x != "", tmp))[::-1])


def error_handler(command, errors, peer_id, **kwargs):
    if "text_args" in errors:
        sendmessage(peer_id, "Укажите нужное сообщение в кавычках.")
    elif "user_ids" in errors:
        if command == "/enable_check_group":
            sendmessage(peer_id, "Здесь Вы должны указать группу, по которой будет введено ограничение вступления в конференцию. Например @testpool , @club1")
        else:
            sendmessage(peer_id, "К данной команде не хватает параметра id пользователей. Например, id1 или по упоминанию @id1 (Павел Дуров)")
    elif "group_ids" in errors:
        sendmessage(peer_id, "Вы должны указать группу. Например: @testpool, https://vk.com/testpool или @club1")
    elif "args" in errors:
        if command == "/addadmin":
            sendmessage(peer_id, "Для данной команды вам нужно указать уровень администрациии. 1 - Moderator, 2 - Administrator.")
        elif command == "/warn_kick_set":
            sendmessage(peer_id, "Укажите количество предупреждений.")
        else:
            sendmessage(peer_id, "Требуется числовой аргумент! Возможно это ID беседы?")
    else:
        sendmessage(peer_id, "Не хватает аргументов: " + str(errors))


def check_permissions_command(command, from_id, chat_id):
    if command in permissions[0]:
        return True
    from_lvl = db.get_level_admin(chat_id, from_id)
    if command in permissions[from_lvl]:
        return True
    elif command in helper_permissions:
        try:
            Helpers.get(user_id=from_id)
            return True
        except Exception as e:
            return False
    else:
        return False


def check_ready_command(command, **kwargs):
    o = len(requirements[command])  # Счетчик Требуемые параметры
    s = 0  # Счетчик Пройденные параметры
    e = []  # Список непройденных параметров
    for i in requirements[command]:
        if kwargs[i]:  # Проверка на существование требования
            s += 1
        else:
            e.append(i)  # Добавление непройденных параметров
    return (o == s, e)


def check_delta_permission(a, b, chat_id):
    return db.get_level_admin(chat_id, a) - db.get_level_admin(chat_id, b)
