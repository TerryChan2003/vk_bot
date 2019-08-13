from utils import *
from module import *
import threading
import os
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from functools import wraps
from pprint import pprint

keyboard_help = VkKeyboard()
keyboard_help.add_button("Помощь по командам", VkKeyboardColor.PRIMARY, payload='"/help"')
keyboard_help.add_line()
keyboard_help.add_button("Скрыть клавиатуру", VkKeyboardColor.DEFAULT, payload='"/clavs"')

default_keyboard = VkKeyboard()
default_keyboard.add_button("Получить должности", VkKeyboardColor.PRIMARY, payload='"/getadmin"')
default_keyboard.add_button("Информация", VkKeyboardColor.NEGATIVE, payload='"/info"')
default_keyboard.add_button("Своя должность", VkKeyboardColor.PRIMARY, payload='"/stat"')
default_keyboard.add_line()
default_keyboard.add_button("Список администраторов", VkKeyboardColor.POSITIVE, payload='"/admins"')
default_keyboard.add_button("ID беседы", VkKeyboardColor.POSITIVE, payload='"/chatid"')
default_keyboard.add_line()
default_keyboard.add_vkapps_button(6973826, groupid, "Открыть сервис", "")
default_keyboard.add_line()
default_keyboard.add_button("Скрыть клавиатуру", VkKeyboardColor.DEFAULT, payload='"/clavs"')

def check_group_verify_permission(f):
    @wraps(f)
    def wrap(chat_id, *args, **kwargs):
        if db.get_chat_group_check(chat_id):
            return f(chat_id=chat_id, *args, **kwargs)
        else:
            sendmessage_chat(chat_id, "Увы, но у Вас не включена проверка по группе. Чтобы воспользоваться командами белого списка Вам нужно включить ограничение с помощью команды \n/enable_check_group @club(Ваш id группы без скобок. Например: @club1) или @(краткое название группы. Например: @testpool)")
    wrap.arguments = f.__code__.co_varnames[:f.__code__.co_argcount]
    return wrap
     
@enable_command_with_permission(3)
def clear(chat_id, from_id, **kwrags):
    text = ""
    for _ in range(0,500):
        text += "&#13;\n"
    sendmessage_chat(chat_id, f"{text}\n{get_ref(from_id)} очистил чат.")

@enable_command_with_permission(4)
@enable_for_helper
def msg_to(args, from_id, text_args, chat_id, **kwargs):
    l = []
    for attach in kwargs["attachments"]:
        if attach["type"] == "photo":
            l.append(get_attachment_photo(attach["photo"]))
    try:
        n = int(args[1])
    except:
        n = 1
    form = get_role(from_id)
    params = dict(
        chat_id=int(args[0]),
        message=f"К Вам обращается {form} с текстом: {text_args[0]}",
        attachment=",".join(l),
        random_id=0
    )
    for i in range(math.ceil(n/10)):
        vk_send_multiple_messages(params, min(n-i*10, 10))
    sendmessage_chat(chat_id, f"Сообщение успешно отправлено")

@enable_command
def online(chat_id, **kwargs):
    member_ids = list(filter(lambda x: x > 0, vk_get_chat_members(chat_id)))
    users = list(filter(lambda x: "last_seen" in x, vk.users.get(user_ids=member_ids, fields="online,last_seen,sex")))
    users_online = list(filter(lambda x: x["online"], users))
    users = list(filter(lambda x: x not in users_online, users))
    l = []
    def get_smile(i):
        tmp = ""
        if "platform" in i["last_seen"]:
            tmp = vk_platforms[i["last_seen"]["platform"]]
        else:
            tmp = "(None)"
        if "online_app" in i:
            app = vk_s.apps.get(app_id=i["online_app"])['items'][0]
            if app['title'] not in ["iPhone", "Android"]:
                tmp += f" (Приложение {app['title']})"
            print("Приложение", i["online_app"])
            pprint(app)
        return tmp
    for i in users_online:
        smile = get_smile(i)
        l.append(f"{i['first_name']} {i['last_name']} - Онлайн {smile}")
    current_datetime = datetime.datetime.now()
    for i in users:
        i["last_seen"]["time"] = current_datetime - datetime.datetime.fromtimestamp(i["last_seen"]["time"])
    for i in sorted(users, key=lambda x: x['last_seen']['time']):
        smile = get_smile(i)
        l.append(f"{i['first_name']} {i['last_name']} - был{sex_str[i['sex']]} в сети {get_format_time(i['last_seen']['time'])} назад {smile}")
    for i in group_words(l, "", delimiter="\n"):
        sendmessage_chat(chat_id, i)



@enable_command_with_permission(3)
def enable_check_group(chat_id, group_ids, **kwargs):
    a = int(group_ids[0])
    if a > 1<<31 - 1:
        sendmessage_chat(chat_id, f"Вы вышли за границы допустимых id групп. Максимальный id {1<<31 -1}")
        return
    g = get_ref(-a)
    whitelist = db.get_whitelist(chat_id)
    for i in vk_get_chat_members(chat_id):
        if whitelist:
            if i in whitelist:
                continue
        if (i < 0) or (i in devspeclist):
            continue
        try:
            if not vk.groups.isMember(user_id=i, group_id=a):
                if vk_member_can_kick(chat_id, i):
                    r = get_ref(i)
                    sendmessage_chat(chat_id, f"{r} не находится в группе {g}")
                    vk.messages.removeChatUser(chat_id=chat_id, user_id=i)
                else:
                    r = get_ref(i, "gen")
                    sendmessage_chat(chat_id, f"Не удается кикнуть {r} он не находится в группе {g}")
        except Exception as e:
            if str(e) == "[15] Access denied: no access to this group":
                sendmessage_chat(chat_id, f"Нет доступа для группы {g}")
                return
    db.set_chat_group_check(chat_id, a)
    sendmessage_chat(chat_id, f"Вы установили для чата доступ исключительно для участников группы {g}")

@enable_command_with_permission(3)
def disable_check_group(chat_id, **kwargs):
    if db.get_chat_group_check(chat_id):
        db.set_chat_group_check(chat_id, 0)
        sendmessage_chat(chat_id, "Вы отключили ограничение доступа вступления в беседу")
    else:
        sendmessage_chat(chat_id, "Ограничение вступления в беседу не включено")

@enable_command_with_permission(4)
def exit_chat(chat_id, args, from_id, **kwargs):
    exit_bot_chat(int(args[0]))
    sendmessage_chat(chat_id, "Успешно вышел из чата")

@enable_command_with_permission(4)
@enable_for_helper
def ckick(args, chat_id, from_id, user_ids, text_args, **kwargs):
    from_chat_id = chat_id
    try:
        chat_id = int(args[0])
    except:
        sendmessage_chat(chat_id, "Требуется числовой id чата")
        return
    form = get_role(from_id)
    for i in user_ids:
        r = get_ref(i)
        if db.get_level_admin(chat_id, i) not in [0, 1, 2, 3]:
            sendmessage_chat(2, "Вы не имеете права кикать спецадминистраторов или разработчиков")
            continue
        if not vk_member_exists(chat_id, int(i)):
            sendmessage_chat(2, f"{r} не существует в конференции под id {chat_id}")
            continue
        if not vk_member_can_kick(chat_id, i):
            sendmessage_chat(2, f"{r} нельзя кикнуть, т.к. он является администратором конференции")
            continue
        sendmessage_chat(2, f"{form} ({get_ref(from_id)}) исключил из беседы {r} (ID: {chat_id}). Комментарий: {text_args[0]}")
        sendmessage_chat(chat_id, f"{r}, {form} исключил Вас из беседы. Комментарий: {text_args[0]}")

        vk.messages.removeChatUser(chat_id=chat_id, member_id=i)



@enable_command_with_permission(4)
@enable_for_helper
def cban(args, chat_id, from_id, user_ids, text_args, **kwargs):
    from_chat_id = chat_id
    try:
        chat_id = int(args[0])
    except:
        sendmessage_chat(chat_id, "Требуется числовой id чата")
        return
    form = get_role(from_id)
    for i in user_ids:
        r = get_ref(i)
        if db.check_ban(chat_id, i):
            sendmessage_chat(2, f"{r} уже заблокирован в данной конференции")
            continue
        if db.get_level_admin(chat_id, i) not in [0, 1, 2, 3]:
            sendmessage_chat(2, "Вы не имеете права кикать спецадминистраторов или разработчиков")
            continue
        if not vk_member_exists(chat_id, int(i)):
            sendmessage_chat(2, f"{r} не существует в конференции под id {chat_id}")
            continue
        if not vk_member_can_kick(chat_id, i):
            sendmessage_chat(2, f"{r} нельзя кикнуть, т.к. он является администратором конференции")
            continue
        sendmessage_chat(2, f"{form} ({get_ref(from_id)}) заблокировал из беседы {r} (ID: {chat_id}). Комментарий: {text_args[0]}")
        sendmessage_chat(chat_id, f"{r}, {form} заблокировал Вас из беседы. Комментарий: {text_args[0]}")
        vk.messages.removeChatUser(chat_id=chat_id, member_id=i)
        db.add_ban(chat_id, i)

@enable_command_with_permission(4)
@enable_for_helper
def caddadmin(args, chat_id, from_id, user_ids, **kwargs):
    from_chat_id = chat_id
    try:
        chat_id = int(args[0])
    except:
        sendmessage_chat(chat_id, "Требуется числовой id чата")
        return
    try:
        level = int(args[1])
    except:
        sendmessage_chat(2, "Требуется указать уровень (вторым числом).")
        return
    form = get_role(from_id)
    for i in user_ids:
        r = get_ref(i, "acc")
        if level >= 4 or level < 0:
            sendmessage_chat(2, "Укажите уровень (0-3).")
            return
        if db.get_level_admin(chat_id, i) not in [0, 1, 2, 3]:
            sendmessage_chat(2, "Вы не имеете права редактировать должности спецадминистраторов и разработчиков")
            continue
        if not vk_member_exists(chat_id, int(i)):
            sendmessage_chat(2, f"{r} не существует в конференции под id {chat_id}")
            continue
        if level == 0: 
            from_id_level = db.get_level_admin(chat_id, i)
            sendmessage_chat(chat_id, f"{form} снял {r} с должности {lvl_name[from_id_level]}")
            sendmessage_chat(2, f"{form} ({get_ref(from_id)}) снял {r} с должности {lvl_name[from_id_level]} ({from_id_level} уровень) (ID: {chat_id})")
            db.remove_admin(chat_id, i)
            return
        sendmessage_chat(2, f"{form} ({get_ref(from_id)}) назначил {r} на должность {lvl_name[level]} ({level} уровень) (ID: {chat_id})")
        if db.add_admin(chat_id, i, level):
            sendmessage_chat(chat_id, f"{form} назначил {r} на должность {lvl_name[level]} ({level} уровень)")
        else:
            db.remove_admin(chat_id, i)
            db.add_admin(chat_id, i, level)
            sendmessage_chat(chat_id, f"{form} назначил {r} на должность {lvl_name[level]} ({level} уровень)")



@enable_command_with_permission(4)
@enable_for_helper
def cwarn(args, chat_id, from_id, user_ids, text_args, **kwargs):
    from_chat_id = chat_id
    try:
        chat_id = int(args[0])
    except:
        sendmessage_chat(chat_id, "Требуется числовой id чата")
        return
    if from_id not in devspeclist:
        helper = db.get_hstats(from_id)
        form = f"Агент поддержки #{helper.id}"
    elif from_id in speclist:
        form = f"Спецадминистратор #{speclist.index(from_id)+1}"
    else:
        form = f"Разработчик #{devlist.index(from_id)+1}"
    for i in user_ids:
        r = get_ref(i)
        if db.get_level_admin(chat_id, i) not in [0, 1, 2, 3]:
            sendmessage_chat(2, "Вы не имеете права выдавать предупреждения спецадминистраторам или разработчикам")
            continue
        if not vk_member_exists(chat_id, int(i)):
            sendmessage_chat(2, f"{r} не существует в конференции под id {chat_id}")
            continue
        sendmessage_chat(2, f"{form} ({get_ref(from_id)}) выдал предупреждение {r} (ID: {chat_id}). Комментарий: {text_args[0]}")
        sendmessage_chat(chat_id, f"{r}, {form} выдал Вам предупреждение. Комментарий: {text_args[0]}")


@enable_command_with_permission(2)
def blist(chat_id, **kwargs):
    r = Ban_List.select().where(Ban_List.chat_id == chat_id)
    if len(r) > 0:
        l = "\n".join([get_ref(i.user_id) for i in r])
        sendmessage_chat(chat_id, f"В списке заблокированных находятся:\n\n{l}")
    else:
        sendmessage_chat(chat_id, "Нет заблокированных пользователей в Вашей конференции")

def check_warn_permission(f):
    @wraps(f)
    def wrap(chat_id, *args, **kwargs):
        if db.get_warn_enabled(chat_id):
            f(chat_id, warn_max=db.get_warn_max(chat_id), *args, **kwargs)
        else:
            sendmessage_chat(chat_id, "В данном чате отключена возможность использования команд для предупреждения. Если она понадобится, то попросите создателя настроить бота через /warn_switch и /warn_kick_set (количество предупреждений для кика)")
    wrap.arguments = f.__code__.co_varnames[:f.__code__.co_argcount]
    return wrap

@enable_command_with_permission(3)
@check_group_verify_permission
def addwhite(chat_id, user_ids, **kwargs):
    for i in user_ids:
        if int(i) in devspeclist:
            continue
        r = get_ref(i)
        if db.add_whitelist(chat_id, int(i)):
            sendmessage_chat(chat_id, f"{r} добавлен в белый список")
        else:
            sendmessage_chat(chat_id, f"{r} уже существует в белом списке")

@enable_command_with_permission(3)
@check_group_verify_permission
def delwhite(chat_id, user_ids, **kwargs):
    a = db.get_chat_group_check(chat_id)
    g = get_ref(-a)
    for i in user_ids:
        r = get_ref(i)
        if db.remove_whitelist(chat_id, int(i)):
            sendmessage_chat(chat_id, f"{r} удален из белого списка")
            if vk_member_exists(chat_id, i):
                if not vk.groups.isMember(user_id=i, group_id=a):
                    if vk_member_can_kick(chat_id, i):
                        r = get_ref(i)
                        sendmessage_chat(chat_id, f"{r} не находится в группе {g}")
                        vk.messages.removeChatUser(chat_id=chat_id, user_id=i)
                    else:
                        r = get_ref(i, "gen")
                        sendmessage_chat(chat_id, f"Не удается кикнуть {r}, но он не находится в группе {g}")
        else:
            sendmessage_chat(chat_id, f"{r} не существует в белом списке")

@enable_command_with_permission(1)
@check_warn_permission
def warn(chat_id, user_ids, from_id, **kwargs):
    warn_max = kwargs["warn_max"]
    for i in user_ids:
        x = get_ref(i, "gen")
        if not vk_member_exists(chat_id, int(i)):
            sendmessage_chat(chat_id, f"{x} нет в конференции")
            continue
        if str(i).startswith("-"):
            sendmessage_chat(chat_id, "Предупреждения не предусмотрены для сообществ!")
            continue
        if check_delta_permission(from_id, i, chat_id) <= 0:
            sendmessage_chat(chat_id, "Вы не имеете право выдать предупреждение выше или равному вам уровню администрации")
            continue
        w = db.add_warn(chat_id, i)
        if w:
            sendmessage_chat(chat_id, f"{get_ref(i)} получил предупреждение [{w.count}/{warn_max}]")
        else:
            try:
                #sendmessage_chat(chat_id, f"Исключаем @id{i} (Пользователя) из беседы за превышение количества предупреждений...")
                vk.messages.removeChatUser(chat_id=chat_id, member_id=i)
                sendmessage_chat(chat_id, f"{get_ref(i)} исключен за превышение количества предупреждений.")
            except Exception as e:
                if str(e) == "[15] Access denied: can't remove this user":
                    sendmessage_chat(chat_id, f"{x} не удалось заблокировать, вероятнее всего он администратор.")
                else:
                    raise e
                continue

@enable_command_with_permission(1)
@check_warn_permission
def unwarn(chat_id, user_ids, from_id, **kwargs):
    warn_max = kwargs["warn_max"]
    for i in user_ids:
        if str(i).startswith("-"):
            sendmessage_chat(chat_id, "Предупреждения не предусмотрены для сообществ!")
            continue
        if check_delta_permission(from_id, i, chat_id) <= 0:
            sendmessage_chat(chat_id, "Вы не имеете право снять предупреждение выше или равному вам уровню администрации")
            continue
        w = db.sub_warn(chat_id, i)
        if w:
            sendmessage_chat(chat_id, f"@id{i} (Пользователю) снято предупреждение {w.count}/{warn_max}")
        else:
            sendmessage_chat(chat_id, "У данного пользователя нет предупреждений")

@enable_command_with_permission(3)
def warn_kick_set(chat_id, args, **kwargs):
    try:
        try:
            count = int(args[0])
        except:
            sendmessage_chat(chat_id, "Пожалуйста перепроверьте аргумент. Он должен быть только числовым!")
            return
        if not (0<count<(1 << 31)):
            sendmessage_chat(chat_id, f"Лимит предупреждений должен быть в интервале [1 ; {(1 << 31) - 1}]")
            return
        db.set_warn_max(chat_id, count)
        sendmessage_chat(chat_id,f"Вы установили лимит для предупреждений {count}")
        l = []
        for i in db.get_warns(chat_id):
            if i.count >= count:
                try:
                    vk.messages.removeChatUser(chat_id=chat_id, member_id=i.user_id)
                    i.count = 0
                    sendmessage_chat(chat_id, f"@id{i.user_id} (Пользователь) был исключен из беседы за превышение количества предупреждений!")
                except:
                    ...
    except Exception as e:
        sendmessage_chat(chat_id, f"Чтото здесь не так... Попробуйте обратиться с /report {e}")

@enable_command_with_permission(3)
def warn_switch(chat_id, **kwargs):
    sendmessage_chat(chat_id,"Набор команд предупреждения были {}".format("включены" if db.set_warn_enabled(chat_id) else "выключены"))

@enable_command_with_permission(1)
def whitelist(chat_id, **kwargs):
    l = []
    whitelist_l = db.get_whitelist(chat_id)
    if whitelist_l:
        for i in db.get_whitelist(chat_id):
            l.append(f"{get_ref(i)}")
        for i in group_words(l, "", delimiter="\n"):
            sendmessage_chat(chat_id, i)
    else:
        sendmessage_chat(chat_id, "Никто не находится в белом списке")

@enable_command_with_permission(0)
@check_warn_permission
def get_warns(chat_id, **kwargs):
    warn_max = kwargs["warn_max"]
    l = []
    if db.get_warns(chat_id).count():
        for i in db.get_warns(chat_id):
            l.append(f"@id{i.user_id} (Пользователь) имеет {i.count} предупреждений из {warn_max} максимальных")
        for i in group_words(l, "", delimiter="\n"):
            sendmessage_chat(chat_id, i)
    else:
        sendmessage_chat(chat_id, "Нет пользователей с предупреждениями")

@enable_command
def open(chat_id, **kwargs):
    sendmessage_chat(chat_id, "Клавиатура показана.", keyboard=default_keyboard.get_keyboard())

@enable_command
def refer_switch(chat_id, from_id, **kwargs):
    r = db.switch_refer(chat_id, from_id)
    if r:
        sendmessage_chat(chat_id, "Вы включили возможность упоминания")
    else:
        sendmessage_chat(chat_id, "Вы отключили возможность упоминания")

@enable_command
def clavs(chat_id, **kwargs):
    sendmessage_chat(chat_id, "Клавиатура скрыта.", keyboard=default_keyboard.get_empty_keyboard())

@enable_command_with_permission(4)
def setavatar(user_ids, text_args, chat_id, **kwargs):
    for i in user_ids:
        try:
            db.update_helpers(i, 'avatar', text_args[0])
            sendmessage_chat(chat_id, 'Аватар агента обновлен.')
        except:
            sendmessage_chat(chat_id, 'Пользователь не является агентом поддержки.')

@enable_command_with_permission(0)
def helpers(chat_id, **kwargs):
    text = "Список агентов поддержки\n\n"
    for i in db.get_helpers():
        x = users_get(i.user_id)
        if not x:
            return
        text += "@id{} ({} {})\n".format(str(x["id"]), x["first_name"], x["last_name"])
    sendmessage_chat(chat_id, text)

@enable_command_with_permission(4)
def del_service(chat_id, user_ids, **kwargs):
    for i in user_ids:
        try:
            db.del_service(i)
            sendmessage_chat(chat_id, "+")
        except:
            sendmessage_chat(chat_id, "-")

@enable_command
def recognize(chat_id, **kwargs):
    os.chdir(tmp_dir)
    for i in kwargs["attachments"]:
        if i["type"] == "audio_message":
            AUDIO_FILE = wget.download(f"{i['audio_message']['link_mp3']}")
            src = AUDIO_FILE
            dst = AUDIO_FILE.split(".")[0] + ".wav"
            sound = AudioSegment.from_mp3(src)
            sound.export(dst, format="wav")
            os.remove(src)
            AUDIO_FILE = dst
            break
    else:
        sendmessage_chat(chat_id, "Аудио сообщение не найдено.")
        return
    r = sr.Recognizer()
    with sr.AudioFile(AUDIO_FILE) as source:
        audio = r.record(source)  # read the entire audio file
    os.remove(AUDIO_FILE)
    try:
        sendmessage_chat(chat_id, f"✉ {r.recognize_google(audio, language='ru-RU')}")
    except sr.UnknownValueError as e:
        sendmessage_chat(chat_id, "Мы не поняли что в данном сообщении")
    except sr.RequestError as e:
        raise e


@enable_command_with_permission(5)
def пиздец(peer_id, **kwargs):
    os.chdir(tmp_dir)
    count = 100
    file = f"hello{threading.get_ident()}.mp3"
    if kwargs["args"]:
        count = int(kwargs["args"][0])
    en_alphavet = [chr(ord("a") + i) for i in range(26)]
    text = "".join([choice(en_alphavet) for _ in range(count)])
    gTTS(text).save(file)
    audio = uploader.audio_message(file, peer_id)
    message = audio["audio_message"]
    vk.messages.send(peer_id=peer_id, message="Вот вам необычное блюдо.", attachment=f"doc{message['owner_id']}_{message['id']}", random_id=get_random_id())
    os.remove(file)

@enable_command
def say_rus(peer_id, raw_text, **kwargs):
    os.chdir(tmp_dir)
    file = f"tmp{threading.get_ident()}.mp3"
    gTTS(raw_text, lang="ru").save(file)
    audio = uploader.audio_message(file, peer_id)
    message = audio["audio_message"]
    vk.messages.send(peer_id=peer_id, message="Ваш озвученный текст", attachment=f"doc{message['owner_id']}_{message['id']}", random_id=get_random_id())
    os.remove(file)

@enable_command
def say_eng(peer_id, raw_text, **kwargs):
    os.chdir(tmp_dir)
    file = f"tmp{threading.get_ident()}.mp3"
    gTTS(raw_text).save(file)
    audio = uploader.audio_message(file, peer_id)
    message = audio["audio_message"]
    vk.messages.send(peer_id=peer_id, message="Ваш озвученный текст", attachment=f"doc{message['owner_id']}_{message['id']}", random_id=get_random_id())
    os.remove(file)

#@enable_command_with_permission(4)
#def ls(chat_id, user_ids, from_id, **kwargs):
#    for z in user_ids:
#        for _ in range(1, 25):
#            sendmessage_chat(chat_id, "@id{}, прочитай лс от vk.com/id".format(str(z))+str(from_id))
#        sendmessage_chat(chat_id, "Думаю, достаточно. Если нет - /ls.")

@enable_command_with_permission(5)
def setrep(user_ids, text_args, chat_id, from_id, **kwargs):
    for i in user_ids:
        if db.get_hstats(i):
            db.update_helpers(i, "reports", int(text_args[0]))
            sendmessage_chat(chat_id, "Репорты @id{} успешно обновлены.".format(i))
        else:
            sendmessage_chat(chat_id, "Пользователь не является агентом поддержки.")

@enable_command_with_permission(4)
def addhelper(chat_id, user_ids, from_id, **kwrags):
    for i in user_ids:
        #if db.get_level_admin(chat_id, i) >= 4:
         #   sendmessage_chat(chat_id, "Его нельзя назначить.")
          #  return
        if not db.get_hstats(i):
            db.add_helper(i, from_id)
            sendmessage_chat(chat_id, "{} был назначен на должность агента поддержки.".format(get_ref(i), str(i)))
        else:
            sendmessage_chat(chat_id, "Пользователь уже является агентом поддержки.")

@enable_command_with_permission(4)
def delhelper(chat_id, user_ids, from_id, **kwrags):
    for i in user_ids:
        if db.get_hstats(i):
            db.del_helper(i)
            sendmessage_chat(chat_id, "{} был снят с должности агента поддержки.".format(get_ref(i), str(i)))
        else:
            sendmessage_chat(chat_id, "Пользователь не является агентом поддержки.")

@enable_command_with_permission(4)
def getinfo(peer_id, args, **kwargs):
    id = int(args[0])
    try:
        name = db.get_title(id)
        photo = db.get_photo(id)
    except:
        sendmessage(peer_id, "Данной конференции не существует в базе данных")
        return
    msg = vk_get_chat_members(id)
    users = ""
    for user_id in msg:
        if str(user_id).startswith("-"):
            continue
        if users == "":
            users += "@id{}".format(user_id)
        else:
            users += ", @id{}".format(user_id)
    sendmessage(peer_id, """ID конференции: {}
        Название конференции: {}
        Фотография конференции: {}
        Участники конференции: {}""".format(id, name, photo, users))

@enable_command_with_permission(2)
def refer(chat_id, from_id, **kwargs):
    user_ids = map(lambda x: f"@id{x}(&#8291;)", filter(lambda x: (x > 0) and (db.check_refer(chat_id, x)), vk_get_chat_members(chat_id)))
    messages = group_words(user_ids, kwargs.get("raw_text") + " " if kwargs.get("raw_text") else ".")
    sendmessage_chat(chat_id, f"@id{from_id} (Пользователь) делает объявление:")
    for i in messages:
        sendmessage_chat(chat_id, i)
    sendmessage_chat(chat_id, "Упоминания разосланы")

@enable_command_with_permission(3)
def addgreeting(chat_id, from_id, raw_text, **kwargs):
    text = raw_text
    if not text:
        sendmessage_chat(chat_id, "Укажите нужное приветствие.")
        return
    if len(text) > 4096:
        sendmessage_chat(chat_id, "Приветствие должно быть не больше 4096 символов!")
        return
    if not db.get_chat_info(chat_id):
        db.add_chat_info(chat_id)
        title = str(db.get_greeting(chat_id))
        db.update_greeting(chat_id, text)
    else:
        db.update_greeting(chat_id, text)
    l = []
    for attach in kwargs["attachments"]:
        if attach["type"] == "photo":
            l.append(get_attachment_photo(attach["photo"]))
    if l:
        db.set_greet_attachments(chat_id, ",".join(l))
    from_id_level = db.get_level_admin(chat_id, from_id)
    x = users_get(from_id, "sex")
    sendmessage_chat(chat_id, "{} @id{} ({} {}) {} приветствие данной конференции.\n\nНовое приветствие: {}".format(lvl_name[from_id_level], x['id'], x['first_name'], x['last_name'],  "обновила" if x['sex'] == 1 else "обновил", text), attachment=",".join(l))

@enable_command_with_permission(3)
def delgreeting(chat_id, from_id, **kwargs):
    from_id_level = db.get_level_admin(chat_id, from_id)
    x = users_get(from_id, "sex")
    try:
        if not db.get_greeting(chat_id) == "":
            print(db.get_greeting)
            db.update_greeting(chat_id, '')
            sendmessage_chat(chat_id, "{} @id{} ({} {}) {} приветствие при приглашении пользователя.".format(lvl_name[from_id_level], x['id'], x['first_name'], x['last_name'], "удалила" if x['sex'] == 1 else "удалил"))
        else:
            sendmessage_chat(chat_id, "Приветствие в конференции не задано.\nЧтобы задать используйте команду - /addgreeting.")
    except:
        sendmessage_chat(chat_id, "Приветствие в конференции не задано.\nЧтобы задать используйте команду - /addgreeting.")

@enable_command_with_permission(2)
def greeting(chat_id, **kwargs):
    try:
        if not db.get_greeting(chat_id) == "":
            sendmessage_chat(chat_id, 'Приветствие в данной конференции - "{}"'.format(db.get_greeting(chat_id)), attachment=db.get_greet_attachments(chat_id))
        else:
            sendmessage_chat(chat_id, "Приветствие в данной конференции не задано.\nЧтобы задать, используйте команду - /addgreeting.")
    except:
        sendmessage_chat(chat_id, "Приветствие в данной конференции не задано.\nЧтобы задать, используйте команду - /addgreeting.")

@enable_command_with_permission(1)
def kick(chat_id, user_ids, from_id, **kwargs):
    for i in user_ids:
        if i == from_id:
            return sendmessage_chat(chat_id, "Вы не можете исключить себя из конференции.")
        x = get_ref(i, "gen")
        if x is None:
            continue
        if  check_delta_permission(from_id, i, chat_id) <= 0:
            sendmessage_chat(chat_id, "Вы не имеете права исключать пользователей выше или равному себе уровню администрации")
            return
        try:
            #sendmessage_chat(chat_id, f"Исключение {x} из конференции...")
            sendmessage_chat(chat_id, f"{get_ref(i)} исключен из беседы")
            vk.messages.removeChatUser(chat_id=chat_id, member_id=i)
            try:
                Admin_List.get(chat_id=chat_id, user_id=i).delete_instance()
            except Exception as e:
                print(e)
        except Exception as e:
            if str(e) == "[15] Access denied: can't remove this user":
                sendmessage_chat(chat_id, f"{x} является администратором беседы")
            elif str(e) == "[935] User not found in chat":
                sendmessage_chat(chat_id, f"{x} нет в конференции")
            else:
                raise e
            continue


@enable_command
def getadmin(chat_id, peer_id, from_id, **kwargs):
    for i in devlist:
        db.add_admin(chat_id, i, 5)
    for i in speclist:
        db.add_admin(chat_id, i, 4)
    ignore = devlist + speclist
    try:
        r = vk.messages.getConversationMembers(peer_id=CHAT_START_ID + chat_id)
    except:
        sendmessage_chat(chat_id, "Не были выданы права администратора, WorldBots не была назначена администратором в самой беседе")
        return
    for i in r["items"]:
        if i["member_id"] in ignore:
            continue
        if "is_owner" in i:
            if db.get_level_admin(chat_id, i["member_id"]) == 3:
                sendmessage_chat(chat_id, "Права уже выданы")
                return
            db.add_admin(chat_id, i["member_id"], 3)
        elif "is_admin" in i:
            db.add_admin(chat_id, i["member_id"], 2)
    sendmessage_chat(chat_id, "Всем администраторам и создателю были выданы должности.", keyboard=keyboard_help.get_keyboard())
    if not db.get_chat_info(chat_id):
        try:
            r = vk.messages.getConversationsById(peer_ids=CHAT_START_ID + chat_id)["items"]
        except Exception as e:
            print(e)
        if r:
            r = r[0]
            pprint(r)
            settings = r["chat_settings"]
            chat_id_info = r["peer"]["id"]
            title = settings["title"]
            photo = settings["photo"]["photo_200"] if "photo" in settings else ""
            db.add_chat_infoex(chat_id_info - CHAT_START_ID, title, photo)

@enable_command_with_permission(3)
def deladmin(chat_id, user_ids, from_id, **kwargs):
    for i in user_ids:
        if i == from_id:
            return sendmessage_chat(chat_id, "Вы не можете снять себя с поста администратора.")
        from_id_level = db.get_level_admin(chat_id, i)
        x = users_get(i)
        if check_delta_permission(from_id, i, chat_id) <= 0:
            sendmessage_chat(chat_id, "Вы не имеете право удалять уровень администрации с пользователей выше или равному себе уровню администрации")
            return
        if db.get_level_admin(chat_id, i):
            sendmessage_chat(chat_id, "@id{} ({} {}) был снят с должности {}.".format(str(x['id']), x['first_name'], x['last_name'], lvl_name[from_id_level]))
            db.remove_admin(chat_id, i)
        else:
            sendmessage_chat(chat_id, "У @id{} (пользователя) нет должностей.".format(i))


@enable_command
def stat(chat_id, from_id, **kwargs):
    if chat_id == 2 and not db.get_level_admin(chat_id, from_id) >= 4:
        sendmessage_chat(chat_id, "Ваша должность - @id{} (Агент поддержки)".format(from_id))
        return
    elif chat_id == 59 and not db.get_level_admin(chat_id, from_id) >= 4:
        sendmessage_chat(chat_id, "Ваша должность - @id{} (Тестер)".format(from_id))
        return
    sendmessage_chat(chat_id, "Ваша должность - @id{} ({})".format(from_id, lvl_name[db.get_level_admin(chat_id, from_id)]))

@enable_command_with_permission(4)
def dellogs(chat_id, **kwargs):
    Logs.delete()
    sendmessage_chat(chat_id, "Логи успешно очищены.")

@enable_command_with_permission(permission=4)
def stats(chat_id, user_ids, from_id, **kwargs):
    for i in user_ids:
        sendmessage_chat(chat_id, "Должность - @id{} ({})".format(i, lvl_name[db.get_level_admin(chat_id, i)]))

@enable_command
def info(chat_id, **kwargs):
    sendmessage_chat(chat_id, "Помощь по командам - /help\nГруппа ВКонтакте: vk.com/world_bots\nПриложение: vk.com/worldbots")


@enable_command
def help(chat_id, from_id, **kwargs):
    from_lvl = db.get_level_admin(chat_id, from_id)
    sendmessage_chat(chat_id, help_list[from_lvl], keyboard=default_keyboard.get_keyboard())


@enable_command_with_permission(3)
def chatid(chat_id, **kwargs):
    sendmessage_chat(chat_id, "ID данного чата - {}".format(chat_id))

@enable_command_with_permission(2)
def title(chat_id, from_id, raw_text, **kwargs):
    text = raw_text
    if not text:
        sendmessage_chat(chat_id, "Укажите нужное название")
        return
    if len(text) > 120:
        sendmessage_chat(chat_id, "Название беседы слишком длинное")
        return
    vk.messages.editChat(chat_id = chat_id, title = text)
    sendmessage_chat(chat_id, "Название конференции было изменено на \"{}\"".format(text))
    if not db.get_chat_info(chat_id):
        db.add_chat_infoex(chat_id, text, "", "", "")
    else:
        db.update_title(chat_id, text)

@enable_command
def report(chat_id, from_id, raw_text, **kwargs):
    text = raw_text
    if db.check_muted_report(from_id):
        sendmessage_chat(chat_id, "Данная команда не доступна для Вас, т. к. были нарушены правила обращения в поддержку")
        return
    x = users_get(from_id)
    report = Reports(user_id = from_id, chat_id = chat_id, text = text)
    report.save()
    sendmessage_chat(chat_id, f"Репорт #{report.id} успешно зарегистрирован.")
    otv = ""
    for i in db.get_reports():
        if i.otext == "":
            otv += "{} ".format(str(i.id))
    if otv == "":
        otv = "-"
    l = []
    for attach in kwargs["attachments"]:
        if attach["type"] == "photo":
            l.append(get_attachment_photo(attach["photo"]))
    sendmessage_chat(2, "[REPORTS] Новый REPORT: {}\nID репорта: {}\nОтправил: @id{} ({} {})\
    \n\nНет ответа: {} ".format(text, report.id, from_id, x['first_name'], x['last_name'], otv), attachment=", ".join(l))

@enable_command
def adm(chat_id, from_id, args, **kwargs):
    if chat_id != 170:
        sendmessage_chat(chat_id, "Данная команда доступна строго в тестовой конференции.")
        return
    try:
        id = int(args[0])
    except:
        sendmessage_chat(chat_id, "Укажите уровень цифрой.")
        return
    if id >= 4 or id < 0:
        sendmessage_chat(chat_id, "Используйте: /adm [уровень (1-3)] (или 0, чтобы снять)")
        return
    from_id_level = db.get_level_admin(chat_id, from_id)
    if id == 0:
        if db.get_level_admin(chat_id, from_id):
            db.remove_admin(chat_id, from_id)
            sendmessage_chat(chat_id, "С Вас была снята должность {}".format(lvl_name[from_id_level]))
            return
        else:
            sendmessage_chat(chat_id, "У Вас нет должностей в беседе.")
            return
    if db.add_admin(chat_id, from_id, id):
        sendmessage_chat(chat_id, "Вам была выдана должность {} ({} уровень)".format(lvl_name[id], str(id)))
    else:
        db.remove_admin(chat_id, from_id)
        db.add_admin(chat_id, from_id, id)
        sendmessage_chat(chat_id, "Вам была выдана должность {} ({} уровень)".format(lvl_name[id], str(id)))

@enable_command_with_permission(3)
def addadmin(chat_id, user_ids, from_id, args, **kwargs):
    try:
        if not int(args[0]):
            sendmessage_chat(chat_id, "Укажите нужный уровень (1-2).")
            return
    except:
        sendmessage_chat(chat_id, "Укажите нужный уровень (1-2).")
        return
    level = int(args[0])
    from_id_level = db.get_level_admin(chat_id, from_id)
    if from_id_level <= level:
        sendmessage_chat(chat_id, "У Вас недостаточно прав на выдачу званий {} и выше.".format(lvl_name[from_id_level]))
        return
    for i in user_ids:
        if str(i).startswith("-"):
            sendmessage_chat(chat_id, "Вы не можете выдать админку сообществу.")
            continue
        if check_delta_permission(from_id, i, chat_id) <= 0:
            sendmessage_chat(chat_id, "Вы не имеете право изменять уровень администрации пользователей выше или равному себе уровню администрации")
            continue
        x = users_get(i, "sex")
        if db.add_admin(chat_id, i, level):
            sendmessage_chat(chat_id, "@id{} ({} {}) {} на должность {}.".format(str(i), x['first_name'], x['last_name'], "назначена" if x['sex'] == 1 else "назначен", lvl_name[level]))
        else:
            db.remove_admin(chat_id, i)
            db.add_admin(chat_id, i, level)
            sendmessage_chat(chat_id, "@id{} ({} {}) {} на должность {}.".format(str(i), x['first_name'], x['last_name'], "назначена" if x['sex'] == 1 else "назначен", lvl_name[level]))


@enable_command
def admins(chat_id, **kwargs):
    r = db.get_admins(chat_id)
    msg = "Chief Administrator:"
    msg1 = "Administrator:"
    msg2 = "Moderator:"
    for i in r:
        if i.level in (1, 2, 3):
            if not db.check_user(i.user_id):
                if str(i.user_id).startswith("-"):
                    continue
                x = users_get(i.user_id, "sex, photo_200")
                if not x or not x.get("photo_200"): continue
                db.add_user(i.user_id, x['first_name'], x['last_name'], x['sex'], x["photo_200"])
                a = db.get_users(i.user_id)
            else:
                a = db.get_users(i.user_id)
            if i.level == 3:
                msg += "\n@id{} ({} {})".format(a.user_id, a.first_name, a.last_name)
            elif i.level == 2:
                msg1 += "\n@id{} ({} {})".format(a.user_id, a.first_name, a.last_name)
            elif i.level == 1:
                msg2 += "\n@id{} ({} {})".format(a.user_id, a.first_name, a.last_name)
    check_it = lambda x, l: x if x != l else ""
    try:
        sendmessage_chat(chat_id, "\n\n".join([check_it(msg, "Chief Administrator:"), check_it(msg1, "Administrator:"), check_it(msg2, "Moderator:")]))
    except:
        sendmessage_chat(chat_id, "Здесь администраторов нет.")

@enable_command_with_permission(2)
def ban(chat_id, user_ids, from_id, **kwargs):
    results = []
    from_r = get_ref(from_id)
    for i in user_ids:
        if db.check_ban(chat_id, i):
            results.append(f"{get_ref(i)} уже находится в списке заблокированных")
        elif i == from_id:
            results.append("Вы не можете заблокировать себя из конференции.")
        elif vk_member_exists(chat_id, int(i)) and not vk_member_can_kick(chat_id, int(i)):
            results.append(f"{get_ref(i, 'gen')} нельзя исключить, т.к. он является администратором.")
        elif db.get_level_admin(chat_id, from_id) <= db.get_level_admin(chat_id, i):
            results.append(f"Вы не можете заблокировать {get_ref(i, 'gen')}, т.к. его уровень администрации выше или равен вашему.")
        else:
            results.append(f"{from_r} заблокировал {get_ref(i, 'gen')}")
            try: vk.messages.removeChatUser(chat_id=chat_id, member_id=i)
            except: ...
            db.remove_admin(chat_id, i)
            db.add_ban(chat_id, i)
    for i in group_words(results, "", delimiter="\n"):
        sendmessage_chat(chat_id, i)
    

@enable_command_with_permission(2)
def unban(chat_id, user_ids, from_id, **kwargs):
    for i in user_ids:
        x = get_ref(i)
        if not db.check_ban(chat_id, i):
            sendmessage_chat(chat_id, f"{x} не заблокирован в данной конференции.")
        else:
            db.remove_ban(chat_id, i)
            sendmessage_chat(chat_id, f"Разблокировали {x} в конференции")

@enable_command_with_permission(4)
@enable_for_helper
def hstats(chat_id, user_ids, **kwargs):
    for i in user_ids:
        if db.get_hstats(i):
            d = db.get_hstats(i)
            z = users_get(i)
            a = users_get(int(d.admin))
            sendmessage_chat(chat_id, "Статистика агента поддержки:\
                \n\nИмя Фамилия: {} {}\nНомер агента: {}\nСтраница ВКонтакте: @id{}\
                \nНазначил: @id{} ({} {})\nДата и время назначения: {}\
                \n\nОтветов на репорт: {}\nВыговоры: {}/3".format(
                    z['first_name'], z['last_name'], str(d.id), z['id'], a['id'], a['first_name'], a['last_name'], d.data, str(d.reports), d.vig))
        else:
            sendmessage_chat(chat_id, "Пользователь не является агентом поддержки.")

@enable_command_with_permission(4)
def hunwarn(chat_id, from_id, user_ids, **kwargs):
    for i in user_ids:
        if db.get_hstats(i):
            d = db.get_hstats(i)
            if d.vig != 0:
                vig = int(d.vig) - 1
                db.update_helpers(i, "vig", vig)
                sendmessage_chat(chat_id, "Вы сняли агенту поддержки @id{} один выговор, теперь у него {}/3 выговоров.".format(i, vig))
            else:
                sendmessage_chat(chat_id, "У агента поддержки 0/3 выговоров.")

@enable_command_with_permission(4)
def hwarn(chat_id, from_id, user_ids, **kwargs):
    for i in user_ids:
        if db.get_hstats(i):
            d = db.get_hstats(i)
            a = users_get(from_id)
            if d.vig != 2:
                vig = int(d.vig) + 1
                db.update_helpers(i, "vig", vig)
                sendmessage_chat(chat_id, "Агент поддержки @id{} получил выговор [{}/3]".format(i, str(vig)))
            else:
                db.del_helper(i)
                sendmessage_chat(chat_id, "Агент поддержки @id{} получил выговор [3/3] и был снят со своего поста.".format(i))
                sendmessage_chat(2, "Руководитель @id{} ({} {}) выдал Вам 3/3 выговоров.\
                \n\n@id{}, команда желает Вам всего самого наилучшего, благодарим за работу! Успехов!".format(
                    a['id'], a['first_name'], a['last_name'], i))
                try:
                    vk.messages.removeChatUser(chat_id = 2, member_id = i)
                except:
                    ...
        else:
            sendmessage_chat(chat_id, "Пользователь не является агентом поддержки.")

@enable_command_with_permission(4)
def check_report(chat_id, args, **kwargs):
    try:
        id = int(args[0])
    except:
        sendmessage_chat(chat_id, "Укажите цифрой.")
        return
    if not db.check_report(id):
        sendmessage_chat(chat_id, "Репорта под данным ID не существует")
        return
    i = db.check_report(id)
    x = users_get(i.helper)
    try:
        sendmessage_chat(chat_id, f"ID репорта: {i.id}\
        \nТекст вопроса: {i.text}\
        \nОтправитель: [id{i.user_id}|@id{i.user_id}] ({i.chat_id} id)\nДата и время: {i.vtime}\
        \n\nОтвет дал: @id{x['id']} ({x['first_name']} {x['last_name']})\
        \nТекст ответа: {i.otext}\nВремя ответа: {i.otime}")
    except:
        sendmessage_chat(chat_id, f"ID репорта: {i.id}\
        \nТекст вопроса: {i.text}\
        \nОтправитель: [id{i.user_id}|@id{i.user_id}] ({i.chat_id} id)\nДата и время: {i.vtime}\n\nОтвет не был дан!")

@enable_command_with_permission(4)
@enable_for_helper
def ans(chat_id, from_id, text_args, args, **kwargs):
    getadm = db.get_level_admin(chat_id, from_id)
    if getadm == 4:
        if not db.get_hstats(from_id):
            db.add_helper(from_id, from_id)
        post = f"спецадминистратора #{speclist.index(from_id)+1}"
    elif getadm == 5:
        if not db.get_hstats(from_id):
            db.add_helper(from_id, from_id)
        post = f"разработчика #{devlist.index(from_id)+1}"
    elif chat_id == 2 and db.get_hstats(from_id):
        sup = db.get_hstats(from_id)
        post = f"агента поддержки #{sup.id}"
    text = text_args[0]
    id = int(args[0])
    if not db.check_report(id):
        sendmessage_chat(chat_id, "Данного ID не существует")
        return
    if db.get_hstats(from_id):
        d = db.get_hstats(from_id)
        rep = int(d.reports) + 1
        db.update_helpers(from_id, "reports", rep)
    i = db.check_report(id)
    if i.otext != "" and getadm <= 3:
        sendmessage_chat(chat_id, "Ответ уже дан.")
        return
    db.update_reports(id, "helper", from_id)
    db.update_reports(id, "otext", text)
    db.update_reports(id, "otime", get_time())
    l = []
    for attach in kwargs["attachments"]:
        if attach["type"] == "photo":
            l.append(get_attachment_photo(attach["photo"]))
    try:
        sendmessage(i.user_id, "Вопрос: {}\nОтвет от {}: {}\n\nС уважением, команда поддержки.".format(i.text, post, text), attachment=",".join(l))
    except:
        sendmessage_chat(i.chat_id, "\nОтправил: @id{}\nВопрос: {}\nОтвет от {}: {}\n\nС уважением, команда поддержки.".format(i.user_id, i.text, post, text), attachment=",".join(l))
    sendmessage_chat(chat_id, "Ответ был успешно отправлен")

@enable_command_with_permission(4)
def allkick(chat_id, user_ids, **kwargs):
    for i in user_ids:
        for z in db.get_chat_infos():
            if i in vk_get_chat_members(z.chat_id):
                if not vk_member_can_kick(z.chat_id, i):
                    sendmessage_chat(chat_id, f"{get_ref(i)} не удалось исключить из беседы #{z.chat_id}")
                else:
                    vk.messages.removeChatUser(chat_id = z.chat_id, member_id = i)
        sendmessage_chat(chat_id, f"{get_ref(i)} исключен из всех возможных бесед")
            

@enable_command_with_permission(5)
def msg(chat_id, raw_text, from_id, **kwargs):
    sendmessage_chat(chat_id, "Началась рассылка сообщений!")
    l = []
    for attach in kwargs["attachments"]:
        if attach["type"] == "photo":
            l.append(get_attachment_photo(attach["photo"]))
    chat_list = []
    for i in db.get_chat_infos():
        if i.chat_id != chat_id:
            chat_list.append(i.chat_id)
    params = dict(
        message=raw_text,
        attachment=",".join(l),
        random_id=0
    )
    for i in range(math.ceil(len(chat_list) / 25)):
        vk_send_multiple_chats(chat_list[25*i:min(25*(i+1), len(chat_list))], params)
    sendmessage_chat(chat_id, "Рассылка чата закончилась!")


@enable_command_with_permission(5)
def get_commands(chat_id, **kwargs):
    sendmessage_chat(chat_id, "\n".join(list(commands.keys())))


@enable_command_with_permission(4)
@enable_for_helper
def unmute_report(chat_id, user_ids, from_id, **kwargs):
    for i in user_ids:
        if db.check_muted_report(i):
            db.remove_muted_report(i)
            x = users_get(i)
            sendmessage_chat(chat_id, "Теперь пользователю @id{} ({} {}) разрешено писать в репорт.".format(x['id'], x['first_name'], x['last_name']))
        else:
            sendmessage_chat(chat_id, "@id{} (Пользователю) не запрещено писать в репорт.".format(i))


@enable_command_with_permission(4)
@enable_for_helper
def mute_report(chat_id, user_ids, from_id, **kwargs):
    for i in user_ids:
        if not db.check_muted_report(i):
            x = users_get(i)
            sendmessage_chat(chat_id, "Теперь пользователю @id{} ({} {}) запрещено писать в репорт.".format(x['id'], x['first_name'], x['last_name']))
            db.add_muted_report(i)
        else:
            sendmessage_chat(chat_id, "@id{} (Пользователю) уже запрещено писать в репорт.".format(i))

@enable_command_with_permission(4)
def addblack(chat_id, user_ids, from_id, **kwargs):
    for i in user_ids:
        if not db.check_black_list(i):
            if check_delta_permission(from_id, i, chat_id) <= 0:
                sendmessage_chat(chat_id, "У Вас недостаточно прав для выполнения данной команды.")
                return
            x = users_get(i)
            sendmessage_chat(chat_id, "@id{} ({} {}) добавлен в черный список бота.".format(x['id'], x['first_name'], x['last_name']))
            db.add_black_list(i)
            try:
                vk.messages.removeChatUser(chat_id = chat_id, member_id = i)
            except:
                  ...
        else:
            sendmessage_chat(chat_id, "@id{} (Пользователь) уже знаходится в черном списке бота.".format(i))

@enable_command_with_permission(4)
def delblack(chat_id, user_ids, from_id, **kwargs):
    for i in user_ids:
        if db.check_black_list(i):
            db.remove_black_list(i)
            x = users_get(i)
            sendmessage_chat(chat_id, "@id{} ({} {}) успешно разблокирован.".format(x['id'], x['first_name'], x['last_name']))
        else:
            sendmessage_chat(chat_id, "@id{} (Пользователь) не находится в черном списке.".format(i))

@enable_command_with_permission(4)
def get_muted_report(chat_id, **kwargs):
    text = "Мут репорта имеют:\n\n"
    for i in db.get_muted_report():
        x = users_get(i.user_id)
        if not x:
            return
        text += "@id{} ({} {})\n".format(str(x["id"]), x["first_name"], x["last_name"])
    sendmessage_chat(chat_id, text)

@enable_command_with_permission(4)
def checkblack(chat_id, **kwargs):
    text = "В черном списке находятся:\n\n"
    for i in db.get_black_list():
        x = users_get(i.user_id)
        if not x:
            return
        text += "@id{} ({} {})\n".format(str(x["id"]), x["first_name"], x["last_name"])
    sendmessage_chat(chat_id, text)


@enable_command_with_permission(5)
def check_chats(chat_id, **kwargs):
    sendmessage_chat(chat_id, "Начинаю сканировать")
    def func():
        chat_ids = []
        peer_ids = tuple(map(lambda x: str(x + CHAT_START_ID), map(lambda x: x.chat_id, Chat_Info.select(Chat_Info.chat_id).order_by(Chat_Info.chat_id))))
        packetes = map(lambda x: vk_get_multiple_chats_info(x), chunk_list(chunk_list(peer_ids, 100), 25))
        for packets in packetes:
            for packet in packets:
                for r in packet["items"]:
                    settings = r["chat_settings"]
                    title = settings["title"]
                    photo = settings["photo"]["photo_200"] if "photo" in settings else "."
                    chat = Chat_Info.get(chat_id=r["peer"]["local_id"])
                    chat.title = title
                    chat.photo = photo
                    chat.save()
                    chat_ids.append(r["peer"]["local_id"])
        sendmessage_chat(chat_id, ",".join(map(str, map(lambda x: x.chat_id, Chat_Info.select(chat_id).where(Chat_Info.chat_id.not_in(chat_ids))))) + " : Заблокировали доступ к беседе")
        for i in tables:
            if hasattr(i, "chat_id"):
                i.delete().where(getattr(i, "chat_id").not_in(chat_ids)).execute()
    func()
    sendmessage_chat(chat_id, "Сканирование завершено")

        
        

@enable_command_with_permission(2)
def akick(chat_id, from_id, **kwargs):
    if db.get_akick(chat_id) == 0:# or db.check_akick(chat_id) == "":
        if not db.get_chat_info(chat_id):
            db.add_chat_info(chat_id)
        db.set_akick(chat_id, 1)
        sendmessage_chat(chat_id, "Вы разрешили исключать пользователей при выходе из конференции.")
    elif db.get_akick(chat_id) == 1:
        if db.get_chat_info(chat_id):
            db.set_akick(chat_id, 0)
        else:
            db.add_chat_info(chat_id)
        sendmessage_chat(chat_id, "Вы запретили исключать пользователей при выходе из конференции.")

@enable_command
def addbug(chat_id, from_id, text_args, args, **kwargs):
    if not chat_id == 59:
        return
    if len(text_args) < 3:
        sendmessage_chat(chat_id, "Недостаточное количество текстовых аргументов! Их требуется 3.  В 1 кавычках опишите суть бага, во 2 кавычках опишите ожидаемый результат, в 3 опишите фактический результат")
        return
    if len(args) < 1:
        sendmessage_chat(chat_id, "Недостаточное количество аргументов! Числом укажите приоритет (1 - низкий, 2 - средний, 3 - высокий, 4 - уязвимость)")
        return
    bug = BugList(from_id=from_id, text=text_args[0], result1=text_args[1], result2=text_args[2], priority=args[0])
    bug.save()
    sendmessage_chat(chat_id, f"Отчет #{bug.id} успешно зарегистрирован")
    sendmessage_chat(2, f"Новый отчет:\n_____________________\
    \n\nID отчета: {bug.id}\nОтправитель: @id{from_id}\nОписание проблемы: {text_args[0]}\nФактический результат: {text_args[1]}\
    \nОжидаемый результат: {text_args[2]}\nЗарегистрирован: {get_time()}\nПриоритет отчета: {bug_priority[int(args[0])]}")

@enable_command
def setstatus(args, chat_id, from_id, **kwargs):
    if db.get_level_admin(chat_id, from_id) == 4:
         dolg = f"Спецадминистратор #{speclist.index(from_id)+1}"
    elif db.get_level_admin(chat_id, from_id) == 5:
        dolg = f"Разработчик #{devlist.index(from_id)+1}"
    elif chat_id == 2:
        sup = db.get_hstats(from_id)
        dolg = f"Агент поддержки #{sup.id}"
    else:
        sendmessage_chat(chat_id, "У Вас нет доступа.")
        return
    try:
        bug_id, to_status = map(int, args)
    except:
        sendmessage_chat(chat_id, "Аргументы должны быть числовыми! Первый id бага и второе цифра статуса")
    try:
        bug = BugList.get_by_id(bug_id)
    except:
        sendmessage_chat(chat_id, "Нет бага под данным id")
        return
    if to_status <= -1 or to_status >= 6:
        sendmessage_chat(chat_id, "Указан неверный статус отчета.")
        return
    tmp = bug.status
    bug.status = to_status
    bug.save()
    sendmessage_chat(chat_id, f"Баг #{bug.id} успешно переведен со статуса {tmp} к {to_status}")
    try:
        vk.messages.send(peer_id = bug.from_id, message = f"{dolg}\n\nОтчет #{bug.id}\
        \nНовый статус отчета - {bug_status[to_status]}", random_id = get_random_id())
    except:
         sendmessage_chat(59, f"{dolg}\n\nОтчет #{bug.id}:\nНовый статус отчета - {bug_status[to_status]}")

@enable_command
def setpriority(chat_id, from_id, args, **kwargs):
    if db.get_level_admin(chat_id, from_id) == 4:
         dolg = f"Спецадминистратор #{speclist.index(from_id)+1}"
    elif db.get_level_admin(chat_id, from_id) == 5:
        dolg = f"Разработчик #{devlist.index(from_id)+1}"
    elif chat_id == 2:
        sup = db.get_hstats(from_id)
        dolg = f"Агент поддержки #{sup.id}"
    else:
        sendmessage_chat(chat_id, "У Вас нет доступа.")
        return
    try:
        bug_id, to_priority = map(int, args)
    except:
        sendmessage_chat(chat_id, "Аргументы должны быть числовыми! Первый id бага и второе цифра статуса")
    try:
        bug = BugList.get_by_id(bug_id)
    except:
        sendmessage_chat(chat_id, "Нет бага под данным id")
        return
    tmp = bug.priority
    bug.priority = to_priority
    bug.save()
    if to_priority <= -1 or to_priority >= 7:
        sendmessage_chat(chat_id, "Указан неверный приоритет отчета.")
        return
    sendmessage_chat(chat_id, f"Баг #{bug.id} успешно переведен с приоритета {tmp} к {to_priority}")
    try:
        vk.messages.send(peer_id = bug.from_id, message = f"{dolg}\n\nОтчет #{bug.id}\
        \nНовый приоритет отчета - {bug_priority[to_priority]}", random_id = get_random_id())
    except:
         sendmessage_chat(59, f"{dolg}\n\nОтчет #{bug.id}:\nНовый приоритет отчета - {bug_priority[to_priority]}")

@enable_command
def getbug(from_id, chat_id, args, **kwargs):
    if not chat_id == 2:
        return sendmessage_chat(chat_id, "У Вас нет прав.")
    try:
        arg = int(args[0])
    except:
        sendmessage_chat(chat_id, "Укажите цифрой.")
        return
    try:
        bug = BugList.get_by_id(arg)
    except:
        sendmessage_chat(chat_id, "Указанный id не найден")
        return
    sendmessage_chat(chat_id, f"ID отчета: {arg}\nОтправитель: @id{bug.from_id}\nОписание проблемы: {bug.text}\nФактический результат: {bug.result1}\
    \nОжидаемый результат: {bug.result2}\nЗарегистрирован: {bug.data}\nПриоритет отчета: {bug_priority[int(bug.priority)]}\nСтатус отчета: {bug_status[int(bug.status)]}")

@enable_command
def comments(from_id, chat_id, args, text_args, **kwargs):
    if db.get_level_admin(chat_id, from_id) == 4:
         dolg = f"Спецадминистратор #{speclist.index(from_id)+1}"
    elif db.get_level_admin(chat_id, from_id) == 5:
        dolg = f"Разработчик #{devlist.index(from_id)+1}"
    elif chat_id == 2:
        sup = db.get_hstats(from_id)
        dolg = f"Агент поддержки #{sup.id}"
    else:
        sendmessage_chat(chat_id, "У Вас нет доступа.")
        return
    try:
        arg = int(args[0])
    except:
        sendmessage_chat(chat_id, "Укажите ID отчета цифрой.")
        return
    try:
        bug = BugList.get_by_id(arg)
    except:
        sendmessage_chat(chat_id, "Такого отчета не существует.")
        return
    try:
        vk.messages.send(peer_id = bug.from_id, message = f"{dolg}:\n{text_args[0]}", random_id = get_random_id())
    except:
        sendmessage_chat(chat_id, f"{dolg}:\n{text_args[0]}")
    sendmessage_chat(chat_id, "Комментарий к отчету отправлен.")