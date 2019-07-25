#!/usr/bin/python3
import time
import datetime
import re
import sqlite3
import os
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll, CHAT_START_ID
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from vk_api import VkApi
from module import Users, Admin_List
import json
import commands
import utils
from utils import *
import sys
import traceback
from pprint import pprint
import random
from threading import Thread
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import importlib

tmp_greet = {}
tmp_chat_msg = {}
msg_limits = 2
warnings_spam = {}


def timing_greet():
    time.sleep(1)
    global tmp_greet
    for i in tmp_greet:
        sendmessage_chat(i, db.get_greeting(i), attachment=db.get_greet_attachments(i))
    tmp_greet = {}


def timing_messages(chat_id, from_id):
    time.sleep(1)
    global tmp_chat_msg
    global warnings_spam
    v = tmp_chat_msg[chat_id][from_id]
    if v > msg_limits:
        sendmessage_chat(2, f"""[ANTI-SPAM] Конференция {chat_id} подозревается в спаме. Сообщений в секунду: {v}, отправители: {get_ref(from_id)}. Дата и время: {get_time()}
Информация о беседе:
Название: {db.get_title(chat_id)}
Количество участников: {len(vk_get_chat_members(chat_id))} """)
        if chat_id in warnings_spam:
            if from_id in warnings_spam[chat_id]:
                warnings_spam[chat_id][from_id] += 1
            else:
                warnings_spam[chat_id][from_id] = 1
        else:
            warnings_spam[chat_id] = {}
            warnings_spam[chat_id][from_id] = 1
        if warnings_spam[chat_id][from_id] >= 3:
            if vk_member_can_kick(chat_id, from_id):
                sendmessage_chat(chat_id, "Мы вынуждены Вас кикнуть из-за спама.")
                sendmessage_chat(2, f"""[ANTI-SPAM] Конференция {chat_id} подозревается в спаме. Сообщений в секунду: {v}, отправители: {get_ref(from_id)}. Дата и время: {get_time()}
Информация о беседе:
Название: {db.get_title(chat_id)}
Количество участников: {len(vk_get_chat_members(chat_id))}
Был исключен из беседы""")
                kick_chat_member(chat_id, from_id)
    del tmp_chat_msg[chat_id][from_id]


bot_longpoll = VkBotLongPoll(session, groupid)
logfile = "log_errors.txt"


def process_user(from_id, chat_id, text):
    global tmp_chat_msg
    if chat_id in tmp_chat_msg:
        if from_id in tmp_chat_msg[chat_id]:
            tmp_chat_msg[chat_id][from_id] += 1
        else:
            tmp_chat_msg[chat_id][from_id] = 1
            Thread(target=timing_messages, args=(chat_id, from_id)).start()
    else:
        tmp_chat_msg[chat_id] = {}
        tmp_chat_msg[chat_id][from_id] = 1
        Thread(target=timing_messages, args=(chat_id, from_id)).start()
    if not db.check_user(from_id):
        if from_id > 0:
            x = users_get(from_id, "sex,photo_200")
            db.add_user(from_id, x['first_name'], x['last_name'], x['sex'], x["photo_200"])
    else:
        Users.update(message_today=Users.message_today + 1,
                     message_week=Users.message_week + 1,
                     message_month=Users.message_month + 1,
                     message_year=Users.message_year + 1).where(Users.user_id == from_id).execute()


def process_chat(peer_id):
    options = {}
    if peer_id > CHAT_START_ID:
        chat_id = peer_id - CHAT_START_ID
        options["chat_id"] = chat_id
        try:
            if not db.get_chat_info(chat_id):
                try:
                    r = vk.messages.getConversationsById(peer_ids=CHAT_START_ID + chat_id)["items"]
                    if r:
                        r = r[0]
                        settings = r["chat_settings"]
                        title = settings["title"]
                        photo = settings["photo"]["photo_200"] if "photo" in settings else ""
                        db.add_chat_infoex(chat_id, title, photo)
                except Exception as e:
                    print(e)
        except:
            ...
    return options


def process_audio_attachments(chat_id, from_id, attachments):
    for i in attachments:
        if i["type"] == "audio_message":
            AUDIO_FILE = wget.download(f"{i['audio_message']['link_mp3']}")
            src = AUDIO_FILE
            dst = AUDIO_FILE.split(".")[0] + ".wav"
            sound = AudioSegment.from_mp3(src)
            sound.export(dst, format="wav")
            os.remove(src)
            AUDIO_FILE = dst
            r = sr.Recognizer()
            with sr.AudioFile(AUDIO_FILE) as source:
                audio = r.record(source)  # read the entire audio file
            os.remove(AUDIO_FILE)
            try:
                sendmessage_chat(chat_id, f"@id{from_id}(✉) {r.recognize_google(audio, language='ru-RU')}")
            except sr.UnknownValueError as e:
                sendmessage_chat(chat_id, "Мы не поняли что в данном сообщении...")
            except sr.RequestError as e:
                raise e


def process_action(chat_id, peer_id, date, from_id, action, attachments):
    if action["type"] in ["chat_invite_user", "chat_invite_user_by_link"]:
        if action["type"] == "chat_invite_user_by_link":
            action['member_id'] = from_id
        r = db.get_chat_group_check(chat_id)
        if r != 0 and action["member_id"] > 0 and action["member_id"] not in devspeclist:
            if action["member_id"] in db.get_whitelist(chat_id):
                sendmessage_chat(chat_id, f"{get_ref(action['member_id'])} проверка пропускается, он находится в белом списке")
            elif not vk.groups.isMember(user_id=action["member_id"], group_id=r):
                sendmessage_chat(chat_id, f"Мы вынуждены Вас исключить, т.к. по правилу конференции Вы не находитесь в группе {get_ref(-r)}")
                vk.messages.removeChatUser(chat_id=chat_id, user_id=action["member_id"])
                return
        # if action['member_id'] == -173243972:
        #    sendmessage(peer_id, "Здравствуйте!\n\nВы добавили меня в Вашу беседу. Для того, чтобы я начал работать, сделайте следующее:\
        #    \n1. Выдайте мне права администратора в данной беседе.\n2. Пропишите команду /getadmin.")
        if db.check_black_list(action['member_id']):
            print(db.check_black_list(action['member_id']).user_id)
            try:
                vk.messages.removeChatUser(chat_id=chat_id, member_id=action["member_id"])
            except:
                ...
            sendmessage_chat(chat_id, "@id{} (Пользователь) был заблокирован разработчиком.\nПригласить его - невозможно".format(action["member_id"]))
        elif db.check_ban(chat_id, action["member_id"]):
            try:
                vk.messages.removeChatUser(chat_id=chat_id, member_id=action["member_id"])
            except:
                ...
            x = users_get([action["member_id"]])
            sendmessage_chat(chat_id, "@id{} ({} {}) заблокирован в данной конференции.".format(str(x['id']), x['first_name'], x['last_name']))
        elif not db.get_greeting(chat_id) == "":
            global tmp_greet
            if chat_id not in tmp_greet:
                if not tmp_greet:
                    Thread(target=timing_greet).start()
                tmp_greet[chat_id] = date
            elif tmp_greet[chat_id] != date:
                sendmessage_chat(chat_id, db.get_greeting(chat_id))
                del tmp_greet[chat_id]
    elif action["type"] == "chat_title_update":
        if db.get_level_admin(chat_id, from_id) <= 1:
            if not db.get_title(chat_id) == "":
                vk.messages.editChat(chat_id=chat_id, title=db.get_title(chat_id))
                sendmessage_chat(chat_id, "У Вас недостаточно прав, чтобы менять название конференции.")
        else:
            db.update_title(chat_id, action["text"])
    elif action["type"] == "chat_kick_user":
        if db.get_level_admin(chat_id, action['member_id']) <= 2:
            db.remove_admin(chat_id, action['member_id'])
        if db.get_akick(chat_id) == 1:
            if db.get_level_admin(chat_id, action['member_id']) == 0:
                try:
                    vk.messages.removeChatUser(chat_id=chat_id, member_id=action['member_id'])
                except:
                    ...
    elif action["type"] == "chat_photo_update":
        max_p = 0
        url = ""
        for i in attachments[0]["photo"]["sizes"]:
            if i["width"] * i["height"] > max_p:
                url = i["url"]
        db.update_photo(chat_id, url)
    elif action["type"] == "chat_photo_remove":
        db.update_photo(chat_id, "")


def process_command(chat_id, raw, text, from_id, peer_id, fwd_messages=None, reply_message=None, **options):
    options["chat_id"] = chat_id
    options.update(raw)
    options["text"] = text
    if len(text.split()) > 1:
        command, args = text.split(" ", 1)
        args = args.strip()
    else:
        command = text.split()[0]
        args = ""
    options["raw_text"] = args
    options["args"] = args
    if command in commands:
        options["command"] = command
        if not check_permissions_command(command, from_id, chat_id):
            sendmessage_chat(chat_id, "У Вас недостаточно прав для выполнения данной команды.")
        else:
            options.update(parseArgs(**options))
            r, e = check_ready_command(**options)
            if not r:
                options["errors"] = e
                error_handler(**options)
            else:
                try:
                    commands[command](**options)
                except Exception as e:
                    traceback.print_exc(file=sys.stdout)
                    sendmessage(peer_id, "Системная ошибка! Пожалуйста, уведомите об этом через команду /report (текст)")


def event_handler(event):
    if event.type == VkBotEventType.MESSAGE_NEW:
        if event.obj.action and event.obj.action["type"] == "chat_invite_user" and event.obj.action["member_id"] == -groupid:
            sendmessage(event.obj.peer_id, "Здравствуйте!\n\nВы добавили меня в Вашу беседу. Для того, чтобы я начал работать, сделайте следующее:\
            \n1. Выдайте мне права администратора в данной беседе.\n2. Пропишите команду /getadmin.")
        if event.obj.peer_id > 2000000000 and not (db.check_chat(event.obj.peer_id - CHAT_START_ID) or str(event.obj.text).startswith("/getadmin") or str(event.obj.text).startswith("/report")):
            print(f"Мошеники!!!!!! {event.obj.peer_id - CHAT_START_ID} {event.obj.from_id} {event.raw}")
            return
        print(event)
        options = {}
        obj = event.obj
        date = obj.date
        from_id = obj.from_id
        peer_id = obj.peer_id
        text = obj.text
        fwd_messages = obj.fwd_messages
        attachments = obj.attachments
        reply_message = obj.reply_message
        payload = obj.payload
        action = obj.action
        options.update(event.raw["object"])
        options["raw"] = event.raw["object"]
        if payload:
            text = json.loads(payload)
            options["text"] = text
        if not attachments:
            if reply_message:
                attachments = reply_message["attachments"]
            elif fwd_messages:
                attachments = fwd_messages[0]["attachments"]
        options["attachments"] = attachments
        if text == "!":
            sendmessage(peer_id, f"Активен. Работаю в стабильном режиме.\n {get_time()}")
            return
        peer_id = peer_id
        r = process_chat(peer_id)
        if "chat_id" in r:
            chat_id = r["chat_id"]
            options["chat_id"] = chat_id
        else:
            #sendmessage(peer_id, "Бот работает исключительно в конференции")
            return
        process_user(from_id, chat_id, text)
        if attachments:
            process_audio_attachments(chat_id, from_id, attachments)
        if action:
            process_action(chat_id, peer_id, date, from_id, action, attachments)
            return
        if text.startswith("/"):
            process_command(**options)


def main():
    for event in bot_longpoll.listen():
        Thread(target=event_handler, args=(event,)).start()


while True:
    try:
        main()
    except KeyboardInterrupt:
        exit(0)
    except:
        ...
