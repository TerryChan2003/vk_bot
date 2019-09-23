from utils import *
from module import *
import threading
import os
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from functools import wraps
from pprint import pprint
from vk_api.bot_longpoll import CHAT_START_ID
from gtts.tts import gTTS
from random import choice
import speech_recognition as sr
from pydub import AudioSegment
from pprint import pprint
import json
import datetime
from functools import wraps

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
            sendmessage_chat(chat_id, "Увы, но у Вас не включена проверка по группе. Чтобы воспользоваться командами белого списка, Вам нужно включить ограничение с помощью команды \n/enable_check_group @club(Ваш id группы без скобок. Например: @club1) или @(краткое название группы. Например: @testpool)")
    wrap.arguments = f.__code__.co_varnames[:f.__code__.co_argcount]
    return wrap

"""@enable_command_with_permission(5)
def test(chat_id, **kwargs):
    sendmessage_chat(chat_id, f"{str(db.get_params(chat_id)['warns'])}")"""

@enable_command_with_permission(5)
def params(chat_id, args, text_args, **kwargs):
    if not (text_args[0].lower() == "kick" or text_args[0].lower() == "ban"):
        return sendmessage_chat(chat_id, "Укажите в кавычках 'kick' или 'ban'")
    if int(args[0]) != 1:
        return sendmessage_chat(chat_id, "Пока можно настраивать только 1 пункт (что делать при достижении макс. кол-ва предупреждений")
    db.set_params(chat_id, {"warns": text_args})
    sendmessage_chat(chat_id, f"Теперь при достижении максимального количества, будет {'исключать из беседы' if text_args[0] == 'kick' else 'блокировать в беседе'} ")

@enable_command_with_permission(4)
def deladmins(chat_id, user_ids, **kwargs):
    for i in user_ids:
        if db.get_level_admin(i) == 5:
            return sendmessage_chat(chat_id, "Не пытайся снять разработчика, напиши Ване, если что-то серьезное")
        admins = db.get_admins_all(i)
        for admin in admins.dicts():
            db.remove_admin(admin.get('chat_id'), i)
        sendmessage_chat(chat_id, f"Пользователь снят с должностей в беседах")

@enable_command_with_permission(5)
@enable_for_helper
def unadm(chat_id, user_ids, **kwargs):
    for i in user_ids:
        r = db.add_admin_helper(chat_id, i)
        if not r:
            return sendmessage_chat(chat_id, "У пользователя не стоит запрет.")
        else:
            sendmessage_chat(chat_id, "Пользователю был снят запрет.")

@enable_command_with_permission(3)
def settitle(chat_id, args, **kwargs):
    try:
        args = int(args[0])
    except:
        return sendmessage_chat(chat_id, "Укажите уровень цифрой")
    if args < 0 or args > 5:
        return sendmessage_chat(chat_id, "Уровень может быть от 0 до 5")
    db.set_settile(chat_id, args)
    sendmessage_chat(chat_id, f"Вы установили доступ к смене названия беседы с {str(args)} уровня")

@enable_command_with_permission(3)
def inviteuser(chat_id, args, **kwargs):
    try:
        args = int(args[0])
    except:
        return sendmessage_chat(chat_id, "Укажите уровень цифрой")
    if args < 0 or args > 5:
        return sendmessage_chat(chat_id, "Уровень может быть от 0 до 5")
    db.set_inviteuser(chat_id, args)
    sendmessage_chat(chat_id, f"Вы установили доступ к приглашению пользователей с {str(args)} уровня")

@enable_command_with_permission(4)
@enable_for_helper
def addrep(from_id, chat_id, args, **kwargs):
    for arg in args:
        if not db.check_report(arg):
            return sendmessage_chat(chat_id, "Репорта с данным ID не существует")
        if db.check_report(arg).otext != "":
            return sendmessage_chat(chat_id, "Репорт уже был отвечен ранее")
        db.update_reports(arg, "otext", "-")
        db.update_reports(arg, "otime", get_time())
        db.update_reports(arg, "helper", from_id)
        sendmessage_chat(chat_id, f"Репорт #{arg} помечен отвеченным")

@enable_command_with_permission(4)
@enable_for_helper
def delreport(chat_id, args, from_id, **kwargs):
    if not db.check_report(args[0]):
        return sendmessage_chat(chat_id, "Репорта с данным ID не существует")
    try:
        sendmessage(db.check_report(args[0]).user_id, f"{get_role(from_id)} удалил Ваш вопрос #{args[0]}")
    except:
        try:
            sendmessage_chat(db.check_report(args[0]).chat_id, f"{get_ref(db.check_report(args[0]).user_id)}, {get_role(from_id)} удалил Ваш вопрос #{args[0]}")
        except:
            ...
    sendmessage_chat(chat_id, f"Репорт #{args[0]} успешно удален")
    db.del_report(args[0])

@enable_command_with_permission(4)
def say(user_ids, chat_id, text_args, **kwargs):
    for i in user_ids:
        try:
            db.add_notification(i, "admin_message", {"text": text_args[0], "actions": []})
            sendmessage_chat(chat_id, "Сообщение отправлено.")
        except:
            sendmessage_chat(chat_id, "Не удалось отправить сообщение. Пользователь не в приложении.")

@enable_command_with_permission(2)
def translation(chat_id, **kwargs):
    if db.get_golos(chat_id):
        db.update_golos(chat_id, False)
        sendmessage_chat(chat_id, "Вы отключили перевод голосовых сообщений в текст")
    elif not db.get_golos(chat_id):
        db.update_golos(chat_id, True)
        sendmessage_chat(chat_id, "Вы включили перевод голосовых сообщений в текст")

@enable_command_with_permission(3)
def clear(chat_id, from_id, **kwrags):
    text = ""
    from_id_level = db.get_level_admin(chat_id, from_id)
    lvl = get_name_adm(chat_id, from_id_level)
    for _ in range(0,500):
        text += "&#13;\n"
    sendmessage_chat(chat_id, f"{text}\n{lvl} {get_ref(from_id)} очистил чат.")

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
                    sendmessage_chat(chat_id, f"Не удается кикнуть {r}, он не находится в группе {g}")
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
            db.remove_admin_helper(chat_id, i)
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
    try:
        chat_id = int(args[0])
    except:
        sendmessage_chat(chat_id, "Требуется числовой id чата")
        return
    form = get_role(from_id)
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
                vk.messages.removeChatUser(chat_id=chat_id, member_id=i)
                r = db.get_params(chat_id)
                if r['warns'][0] == 'kick':
                    sendmessage_chat(chat_id, f"{get_ref(i)} исключен за превышение количества предупреждений.")
                elif r['warns'][0] == 'ban':
                    sendmessage_chat(chat_id, f"{get_ref(i)} заблокирован за превышение количества предупреждений.")
                    db.remove_admin(chat_id, i)
                    db.add_ban(chat_id, i)
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
            sendmessage_chat(chat_id, "Пожалуйста, перепроверьте аргумент. Он должен быть только числовым!")
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
        sendmessage_chat(chat_id, f"Что-то здесь не так... Попробуйте обратиться с /report {e}")

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

@enable_command_with_permission(1)
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

@enable_command_with_permission(4)
@enable_for_helper
def helpers(chat_id, **kwargs):
    if chat_id != 2:
        return sendmessage_chat(chat_id, "Команда не уйдет дальше беседы агентов")
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

@enable_command_with_permission(4)
def ls(chat_id, user_ids, from_id, **kwargs):
    if int(from_id) == 448368288:
        sendmessage_chat("Нет. Пожалуйста. НЕТ!")
        vk.messages.sendSticker(sticker_id=12440, chat_id=chat_id, random_id=get_random_id())
        return
    for z in user_ids:
        params = dict(
            chat_id=int(chat_id),
            message=f"@id{str(z)}, прочитай лс от vk.com/id{str(from_id)}",
            random_id=0
        )
        for i in range(math.ceil(25 / 10)):
            vk_send_multiple_messages(params, min(25 - i * 10, 10))
        sendmessage_chat(chat_id, "Думаю, достаточно. Если нет - /ls.")

@enable_command_with_permission(5)
def givepoint(user_ids, chat_id, args, **kwargs):
    for i in user_ids:
        if not db.get_tester(i):
            sendmessage_chat(chat_id, "Пользователь не является тестером.")
            return
        if db.get_tester(i).kick:
            sendmessage_chat(chat_id, "Пользователь исключен из программы тестирования.")
            return
        r = db.get_balls(i)
        r = r+int(args[0])
        db.update_testers(i, "points", r)
        sendmessage_chat(chat_id, f"Тестеру начислено {args[0]} баллов. У него всего: {r}")
        try:
            sendmessage(i, f"Сообщество WORLD BOTS начислило Вам {args[0]} баллов")
        except:
            sendmessage_chat(59, f'Сообщество WORLD BOTS начислило {get_ref(i, "dat")} {args[0]} баллов')

@enable_command_with_permission(4)
def getpoint(user_ids, chat_id, **kwargs):
    for i in user_ids:
        r = db.get_tester(i)
        if not r:
            return sendmessage_chat(chat_id, "Пользователь не является тестером")
        if r.kick:
            return sendmessage_chat(chat_id, "Пользователь был исключен из программы тестирования.")
        sendmessage_chat(chat_id, f"У тестера {r.points} баллов")

@enable_command_with_permission(5)
def setrep(user_ids, args, chat_id, **kwargs):
    for i in user_ids:
        if db.get_hstats(i):
            db.update_helpers(i, "reports", int(args[0]))
            sendmessage_chat(chat_id, "Репорты @id{} успешно обновлены.".format(i))
        else:
            sendmessage_chat(chat_id, "Пользователь не является агентом поддержки.")



@enable_command_with_permission(4)
def addtester(chat_id, user_ids, from_id, **kwargs):
    for i in user_ids:
        if not db.check_user(i):
            r = users_get(i, "photo_200, sex")
            db.add_user(i, r['first_name'], r['last_name'], r['sex'], r['photo_200'])
        if not db.get_tester(i):
            db.add_tester(i, from_id)
            sendmessage_chat(chat_id, f"{get_ref(i)} был назначен на должность тестера.")
        else:
            if not db.get_tester(i).kick:
                return sendmessage_chat(chat_id, "Пользователь уже является тестером.")
            sendmessage_chat(chat_id, "Пользователь уже являлся тестером. Переназначили")
            db.update_testers(i, "kick", False)
            db.update_testers(i, "akick", 0)
            db.update_testers(i, "reason", "None")
            db.update_testers(i, "data", get_time())

@enable_command_with_permission(4)
def addhelper(chat_id, user_ids, from_id, **kwrags):
    for i in user_ids:
        r = db.get_hstats(i)
        if not r:
            db.add_helper(i, from_id)
            sendmessage_chat(chat_id, "{} был назначен на должность агента поддержки.".format(get_ref(i)))
        else:
            sendmessage_chat(chat_id, f"Пользователь уже являлся агентом поддержки. Переназначили.\
                                      \nСнят был за {r.areason}, руководителем {get_ref(r.akick)}, дата: {r.atime}")
            db.update_helpers(i, "kick", False)
            db.update_helpers(i, "akick", 0)
            db.update_helpers(i, "areason", "None")
            db.update_helpers(i, "data", get_time())
            db.update_helpers(i, "adata", 0)

@enable_command_with_permission(4)
def deltester(chat_id, user_ids, from_id, text_args, **kwargs):
    for i in user_ids:
        if db.get_tester(i):
            db.update_testers(i, "kick", True)
            db.update_testers(i, "akick", from_id)
            db.update_testers(i, "reason", text_args[0])
            sendmessage_chat(chat_id, f"{get_ref(i)} снят с должности тестера.")
        else:
            sendmessage_chat(chat_id, "Пользователь не является тестером.")

@enable_command_with_permission(4)
def delhelper(chat_id, user_ids, text_args, from_id, **kwrags):
    for i in user_ids:
        if db.get_hstats(i):
            db.del_helper(i, from_id, text_args[0])
            sendmessage_chat(chat_id, "{} был снят с должности агента поддержки.".format(get_ref(i), str(i)))
        else:
            sendmessage_chat(chat_id, "Пользователь не является агентом поддержки.")

@enable_command_with_permission(4)
@enable_for_helper
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
def setname(chat_id, args, text_args, from_id, **kwargs):
    if not db.get_level_adm(chat_id).setlevel:
        return sendmessage_chat(chat_id, "У Вас нет доступа для смены названия уровня.\nЕсли хотите получить его, обратитесь в поддержку - /report")
    if db.get_level_admin(chat_id, from_id) == 3 and int(args[0]) >= 4:
        return sendmessage_chat(chat_id, "Нет прав для смены этих названий.")
    if int(args[0]) > 5 or int(args[0]) < 0:
        return sendmessage_chat(chat_id, "Уровень можно менять от 0 до 5.")
    if len(text_args[0]) <= 2:
        return sendmessage_chat(chat_id, "Название не может быть меньше 2 символов.")
    db.update_name(chat_id, int(args[0]), str(text_args[0]))
    sendmessage_chat(chat_id, f"{str(args[0])} уровню выдано название {text_args[0]}")

@enable_command_with_permission(2)
def getname(chat_id, args, **kwargs):
    args = int(args[0])
    r = get_name_adm(chat_id, args)
    sendmessage_chat(chat_id, f"Название {str(args)} уровня: {r}")

@enable_command_with_permission(4)
@enable_for_helper
def setlevel(chat_id, args, **kwargs):
    if db.get_level_adm(int(args[0])).setlevel:
        db.set_setlevel(int(args[0]))
        sendmessage_chat(chat_id, f"Вы забрали возможность менять названия уровней в беседе #{str(args[0])}")
    elif not db.get_level_adm(int(args[0])).setlevel:
        db.set_setlevel(int(args[0]), True)
        sendmessage_chat(chat_id, f"Вы выдали возможность менять названия уровней в беседе #{str(args[0])}")

@enable_command_with_permission(3)
def addgreeting(chat_id, from_id, raw_text, **kwargs):
    text = raw_text
    if not text:
        sendmessage_chat(chat_id, "Укажите нужное приветствие.")
        return
    if len(text) > 4096:
        sendmessage_chat(chat_id, "Приветствие должно быть не больше 4096 символов!")
        return
    from_id_level = db.get_level_admin(chat_id, from_id)
    lvl = get_name_adm(chat_id, from_id_level)
    if not db.get_chat_info(chat_id):
        db.add_chat_info(chat_id)
        db.update_greeting(chat_id, text)
    else:
        db.update_greeting(chat_id, text)
    l = []
    for attach in kwargs["attachments"]:
        if attach["type"] == "photo":
            l.append(get_attachment_photo(attach["photo"]))
    if l:
        db.set_greet_attachments(chat_id, ",".join(l))
    x = users_get(from_id, "sex")
    sendmessage_chat(chat_id, "{} @id{} ({} {}) {} приветствие данной конференции.\n\nНовое приветствие: {}".format(lvl, x['id'], x['first_name'], x['last_name'],  "обновила" if x['sex'] == 1 else "обновил", text), attachment=",".join(l))


@enable_command_with_permission(3)
def delgreeting(chat_id, from_id, **kwargs):
    x = users_get(from_id, "sex")
    from_id_level = db.get_level_admin(chat_id, from_id)
    lvl = get_name_adm(chat_id, from_id_level)
    try:
        if not db.get_greeting(chat_id) == "":
            print(db.get_greeting)
            db.update_greeting(chat_id, '')
            sendmessage_chat(chat_id, "{} @id{} ({} {}) {} приветствие при приглашении пользователя.".format(lvl, x['id'], x['first_name'], x['last_name'], "удалила" if x['sex'] == 1 else "удалил"))
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

"""@enable_command_with_permission(4)
def kicks(chat_id, user_ids, from_id, raw_text, **kwargs):
    sendmessage_chat(chat_id, f"raw_text: {raw_text}")
    for i in user_ids:
        if i == from_id:
            sendmessage_chat(chat_id, "Вы не можете исключить себя из конференции.")
        x = get_ref(i)
        if x is None:
            continue
        if  check_delta_permission(from_id, i, chat_id) <= 0:
            sendmessage_chat(chat_id, f"У Вас недостаточно прав для исключения {get_ref(i, 'gen')}")
            continue
        try:
            vk.messages.removeChatUser(chat_id=chat_id, member_id=i)
            sendmessage_chat(chat_id, f"{x} исключен из беседы")
            try:
                Admin_List.get(chat_id=chat_id, user_id=i).delete_instance()
            except Exception as e:
                print(e)
        except Exception as e:
            if str(e) == "[15] Access denied: can't remove this user":
                sendmessage_chat(chat_id, f"{x} является администратором беседы")
            elif str(e) == "[935] User not found in chat":
                sendmessage_chat(chat_id, f"{x} нет состоит в беседе")
            else:
                raise e
            continue"""

@enable_command_with_permission(1)
def kick(chat_id, user_ids, from_id, **kwargs):
    results = []
    for i in user_ids:
        x = get_ref(i)
        if x is None:
            continue
        if  check_delta_permission(from_id, i, chat_id) <= 0:
            results.append(f"У Вас недостаточно прав для исключения {get_ref(i, 'gen')}")
            continue
        try:
            vk.messages.removeChatUser(chat_id=chat_id, member_id=i)
            results.append(f"{x} исключен из беседы")
            try:
                Admin_List.get(chat_id=chat_id, user_id=i).delete_instance()
            except Exception as e:
                print(e)
        except Exception as e:
            if str(e) == "[15] Access denied: can't remove this user":
                results.append(f"{x} является администратором беседы")
            elif str(e) == "[935] User not found in chat":
                results.append(f"{x} нет состоит в беседе")
            else:
                raise e
            continue
    for z in group_words(results, "", delimiter="\n"):
        sendmessage_chat(chat_id, z)


@enable_command
def getadmin(chat_id, from_id, **kwargs):
    for i in devlist:
        db.add_admin(chat_id, i, 5)
    for i in speclist:
        db.add_admin(chat_id, i, 4)
    ignore = devlist + speclist
    try:
        r = vk.messages.getConversationMembers(peer_id=CHAT_START_ID + chat_id)
    except:
        sendmessage_chat(chat_id, "Не были выданы права администратора, WorldBots не был назначен администратором в самой беседе")
        return
    for i in r["items"]:
        if i["member_id"] in ignore:
            continue
        if db.get_info_admin(chat_id, i) and db.get_level_admin(chat_id, from_id) < 4:
            sendmessage_chat(chat_id, f"{get_ref(i)} был снят с должности администратора агентом поддержки.\
                                         \nЕсли Вы не согласны - обратитесь в /report или в личные сообщения сообщества")
            return
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
            sendmessage_chat(2, f"Новая беседа #{str(chat_id_info - CHAT_START_ID)}: {r['title']}")

@enable_command_with_permission(3)
def deladmin(chat_id, user_ids, from_id, **kwargs):
    results = []
    for i in user_ids:
        if i == from_id:
            results.append("Вы не можете снять себя с поста администратора.")
            continue
        from_id_level = db.get_level_admin(chat_id, i)
        lvl = get_name_adm(chat_id, from_id_level)
        x = users_get(i)
        if check_delta_permission(from_id, i, chat_id) <= 0:
            results.append("Вы не имеете право удалять уровень администрации с пользователей выше или равному себе уровню администрации")
            continue
        if db.get_level_admin(chat_id, i):
            results.append("@id{} ({} {}) был снят с должности {}.".format(str(x['id']), x['first_name'], x['last_name'], lvl))
            db.remove_admin(chat_id, i)
        else:
            results.append("У @id{} (пользователя) нет должностей.".format(i))
    for z in group_words(results, "", delimiter="\n"):
        sendmessage_chat(chat_id, z)


@enable_command
def stat(chat_id, from_id, **kwargs):
    if (db.get_hstats(from_id) and not db.get_hstats(from_id).kick) and not db.get_level_admin(chat_id, from_id) >= 4 and chat_id == 2:
        sendmessage_chat(chat_id, "Ваша должность - @id{} (Агент поддержки)".format(from_id))
        return
    from_id_level = db.get_level_admin(chat_id, from_id)
    lvl = get_name_adm(chat_id, from_id_level)
    sendmessage_chat(chat_id, "Ваша должность - @id{} ({})".format(from_id, lvl))

"""
@enable_command_with_permission(4)
def dellogs(chat_id, **kwargs):
    Logs.delete()
    sendmessage_chat(chat_id, "Логи успешно очищены.")
"""

@enable_command_with_permission(permission=4)
def stats(chat_id, user_ids, **kwargs):
    for i in user_ids:
        sendmessage_chat(chat_id, "Должность - @id{} ({})".format(i, get_name_adm(chat_id, db.get_level_admin(chat_id, i))))

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

@enable_command_with_permission(4)
@enable_for_helper
def addticket(user_ids, chat_id, args, text_args, from_id, **kwargs):
    for i in user_ids:
        r = Reports(user_id = i, chat_id = args[0], text = text_args[0])
        r.save()
        sendmessage_chat(chat_id, f"Репорт от имени администрации #{r.id} зарегистрирован.")
        try:
            sendmessage(i, f"От Вашего имени был создан репорт (создал {get_role(from_id)})\n\nТекст: {text_args[0]}")
        except:
            try:
                sendmessage_chat(args[0], f"{get_ref(i)}, от Вашего имени был создан тиккет-запрос.\
                \n\nСоздал: {get_role(from_id)}\nТекст: {text_args[0]}")
            except:
                sendmessage_chat(chat_id, "Тиккет создан, но отправить человеку не получилось :(")

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
        if db.get_info_admin(chat_id, i) and db.get_level_admin(chat_id, from_id) < 4:
            sendmessage_chat(chat_id, "Пользователь был снят с должности администратора агентом поддержки.\
                                         \nЕсли Вы не согласны - обратитесь в /report или в личные сообщения сообщества")
            return
        lvl = get_name_adm(chat_id, level)
        if str(i).startswith("-"):
            sendmessage_chat(chat_id, "Вы не можете выдать админку сообществу.")
            continue
        if check_delta_permission(from_id, i, chat_id) <= 0:
            sendmessage_chat(chat_id, "Вы не имеете право изменять уровень администрации пользователей выше или равному себе уровню администрации")
            continue
        x = users_get(i, "sex")
        if db.add_admin(chat_id, i, level):
            sendmessage_chat(chat_id, "@id{} ({} {}) {} на должность {}.".format(str(i), x['first_name'], x['last_name'], "назначена" if x['sex'] == 1 else "назначен", lvl))
        else:
            db.remove_admin(chat_id, i)
            db.add_admin(chat_id, i, level)
            sendmessage_chat(chat_id, "@id{} ({} {}) {} на должность {}.".format(str(i), x['first_name'], x['last_name'], "назначена" if x['sex'] == 1 else "назначен", lvl))


@enable_command_with_permission(4)
@enable_for_helper
def cadmins(chat_id, args, **kwargs):
    r = db.get_admins(args[0])
    msg = f"{get_name_adm(args[0], 3)}:"
    msg1 = f"{get_name_adm(args[0], 2)}:"
    msg2 = f"{get_name_adm(args[0], 1)}:"
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
        sendmessage_chat(chat_id, "\n\n".join(
            [check_it(msg, f"{get_name_adm(chat_id, 3)}:"), check_it(msg1, f"{get_name_adm(chat_id, 2)}:"),
             check_it(msg2, f"{get_name_adm(chat_id, 1)}:")]))
    except:
        sendmessage_chat(chat_id, "Здесь администраторов нет.")

@enable_command
def admins(chat_id, **kwargs):
    r = db.get_admins(chat_id)
    msg = f"{get_name_adm(chat_id, 3)}:"
    msg1 = f"{get_name_adm(chat_id, 2)}:"
    msg2 = f"{get_name_adm(chat_id, 1)}:"
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
        sendmessage_chat(chat_id, "\n\n".join([check_it(msg, f"{get_name_adm(chat_id, 3)}:"), check_it(msg1, f"{get_name_adm(chat_id, 2)}:"), check_it(msg2, f"{get_name_adm(chat_id, 1)}:")]))
    except:
        sendmessage_chat(chat_id, "Здесь администраторов нет.")

@enable_command_with_permission(2)
def ban(chat_id, user_ids, from_id, **kwargs):
    results = []
    from_r = get_ref(from_id)
    for i in user_ids:
        if db.check_ban(chat_id, i):
            results.append(f"{get_ref(i)} уже находится в списке заблокированных")
        elif vk_member_exists(chat_id, int(i)) and not vk_member_can_kick(chat_id, int(i)):
            results.append(f"{get_ref(i, 'gen')} нельзя исключить, т.к. он является администратором.")
        elif db.get_level_admin(chat_id, from_id) <= db.get_level_admin(chat_id, i):
            results.append(f"Вы не можете заблокировать {get_ref(i, 'gen')}, т.к. его уровень администрации выше или равен Вашему.")
        else:
            results.append(f"{from_r} заблокировал {get_ref(i, 'gen')}")
            try: vk.messages.removeChatUser(chat_id=chat_id, member_id=i)
            except: ...
            db.remove_admin(chat_id, i)
            db.add_ban(chat_id, i)
    for i in group_words(results, "", delimiter="\n"):
        sendmessage_chat(chat_id, i)
    

@enable_command_with_permission(2)
def unban(chat_id, user_ids, **kwargs):
    results = []
    for i in user_ids:
        x = get_ref(i)
        if not db.check_ban(chat_id, i):
            results.append(f"{x} не заблокирован в данной беседе.")
        else:
            db.remove_ban(chat_id, i)
            results.append(f"Разблокировали {x} в беседе")
    for i in group_words(results, "", delimiter="\n"):
        sendmessage_chat(chat_id, i)

@enable_command_with_permission(4)
@enable_for_helper
def hstats(chat_id, user_ids, **kwargs):
    results = []
    for i in user_ids:
        if db.get_hstats(i):
            d = db.get_hstats(i)
            z = users_get(i)
            a = users_get(int(d.admin))
            if d.kick:
                results.append(f"Агент поддержки был снят.\
                \nПричина: {d.areason}, руководителем {get_ref(d.akick)}, дата: {d.atime}")
            sendmessage_chat(chat_id, "Статистика агента поддержки:\
                \n\nИмя Фамилия: {} {}\nНомер агента: {}\nСтраница ВКонтакте: @id{}\
                \nНестандартное название: {}\
                \nНазначил: @id{} ({} {})\nДата и время назначения: {}\
                \n\nОтветов на репорт: {}\nВыговоры: {}/3".format(
                    z['first_name'], z['last_name'], str(d.id), z['id'], d.name if d.name != "None" else "Отсутствует", a['id'], a['first_name'], a['last_name'], d.data, str(d.reports), d.vig))
        else:
            results.append(f"{get_ref(i)} не является агентом поддержки.")
    for i in group_words(results, "", delimiter="\n"):
        sendmessage_chat(chat_id, i)

@enable_command_with_permission(4)
def hunwarn(chat_id, from_id, user_ids, **kwargs):
    results = []
    for i in user_ids:
        if db.get_hstats(i):
            d = db.get_hstats(i)
            if d.vig != 0:
                vig = int(d.vig) - 1
                db.update_helpers(i, "vig", vig)
                results.append("Вы сняли {} один выговор, теперь у него {}/3 выговоров.".format(get_ref(i, 'dat'), vig))
            else:
                results.append(f"У {get_ref(i, 'gen')} 0/3 выговоров.")
    for i in group_words(results, "", delimiter="\n"):
        sendmessage_chat(chat_id, i)

@enable_command_with_permission(4)
def hwarn(chat_id, from_id, user_ids, **kwargs):
    results = []
    for i in user_ids:
        if db.get_hstats(i):
            d = db.get_hstats(i)
            a = users_get(from_id)
            if d.vig != 2:
                vig = int(d.vig) + 1
                db.update_helpers(i, "vig", vig)
                results.append("Агент поддержки {} получил выговор [{}/3]".format(get_ref(i), str(vig)))
            else:
                db.del_helper(i, from_id, "3/3 выговоров")
                results.append("Агент поддержки {} получил выговор [3/3] и был снят со своего поста.".format(i))
                sendmessage_chat(2, "Руководитель @id{} ({} {}) выдал Вам 3/3 выговоров.\
                \n\n@id{}, команда желает Вам всего самого наилучшего, благодарим за работу! Успехов!".format(
                    a['id'], a['first_name'], a['last_name'], i))
                try:
                    vk.messages.removeChatUser(chat_id = 2, member_id = i)
                except:
                    ...
        else:
            results.append("Пользователь не является агентом поддержки.")
    for i in group_words(results, "", delimiter="\n"):
        sendmessage_chat(chat_id, i)

@enable_command_with_permission(4)
def getnumber(chat_id, args, **kwargs):
    id = db.get_helper_by_id(args[0])
    if not id:
        return sendmessage_chat(chat_id, "Агент не найден.")
    sendmessage_chat(chat_id, f'Номер {args[0]} принадлежит {get_ref(id.user_id)}')

@enable_command_with_permission(4)
def gethname(chat_id, raw_text, **kwargs):
    id = db.get_helper_by_name(raw_text)
    if not id:
        return sendmessage_chat(chat_id, "Агент не найден.")
    sendmessage_chat(chat_id, f'Имя {raw_text} принадлежит {get_ref(id.user_id)}')

@enable_command_with_permission(4)
@enable_for_helper
def check_report(chat_id, args, **kwargs):
    results = []
    for arg in args:
        if not db.check_report(arg):
            results.append(f"Репорта #{str(arg)} не существует")
            return
        i = db.check_report(arg)
        x = users_get(i.helper)
        try:
            results.append(f"ID репорта: {i.id}\
            \nТекст вопроса: {i.text}\
            \nОтправитель: [id{i.user_id}|@id{i.user_id}] ({i.chat_id} id)\nДата и время: {i.vtime}\
            \n\nОтвет дал: @id{x['id']} ({x['first_name']} {x['last_name']})\
            \nТекст ответа: {i.otext}\nВремя ответа: {i.otime}")
        except:
            results.append(f"ID репорта: {i.id}\
            \nТекст вопроса: {i.text}\
            \nОтправитель: [id{i.user_id}|@id{i.user_id}] ({i.chat_id} id)\nДата и время: {i.vtime}\n\nОтвет не был дан!")
    for i in group_words(results, "", delimiter="\n"):
        sendmessage_chat(chat_id, i)

@enable_command_with_permission(5)
def givename(user_ids, chat_id, text_args, **kwargs):
    for i in user_ids:
        if not db.get_hstats(i):
            return sendmessage_chat(chat_id, "Пользователь не является агентом поддержки.")
        if db.get_hstats(i).akick:
            return sendmessage_chat(chat_id, "Пользователь был снят с должности агента поддержки.")
        db.update_helpers(i, "name", text_args[0])
        sendmessage_chat(chat_id, "Имя агента успешно обновлено.")

@enable_command_with_permission(4)
@enable_for_helper
def ans(chat_id, from_id, text_args, args, **kwargs):
    if db.get_hstats(from_id) and db.get_level_admin(chat_id, from_id) <= 3 and chat_id != 2:
        return sendmessage_chat(chat_id, "На Вашем месте я бы перешел в нужную беседу.")
    if "с уважением" in text_args[0].lower():
        sendmessage_chat(chat_id, "Возможно, стоит перечитать FAQ перед тем как отвечать на репорты.")
        return
    post = get_role(from_id)
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
    getadm = db.get_level_admin(chat_id, from_id)
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
        sendmessage(i.user_id, "Вопрос: {}\nОтвет дал {}: {}\n\nС уважением, команда поддержки.".format(i.text, post, text), attachment=",".join(l))
    except:
        try:
            sendmessage_chat(i.chat_id, "\nОтправил: @id{}\nВопрос: {}\nОтвет дал {}: {}\n\nС уважением, команда поддержки.".format(i.user_id, i.text, post, text), attachment=",".join(l))
        except:
            sendmessage_chat(chat_id, "Нет прав, но ответ записал в сервис.")
    if len(text_args[0]) < 15:
        sendmessage_chat(26, f"[ANS] Подозрительный ответ:\n\n{text}\nОтветил: {get_ref(from_id)}")
    sendmessage_chat(chat_id, "Ответ был успешно отправлен")

@enable_command_with_permission(5)
def msg(chat_id, raw_text, **kwargs):
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
def unmute_report(chat_id, user_ids, **kwargs):
    results = []
    for i in user_ids:
        if db.check_muted_report(i):
            db.remove_muted_report(i)
            x = get_ref(i)
            results.append(f"Теперь пользователю {x} разрешено писать в репорт.")
        else:
            results.append("@id{} (Пользователю) не запрещено писать в репорт.".format(i))
    for i in group_words(results, "", delimiter="\n"):
        sendmessage_chat(chat_id, i)

@enable_command_with_permission(4)
@enable_for_helper
def mute_report(chat_id, user_ids, **kwargs):
    results = []
    for i in user_ids:
        if not db.check_muted_report(i):
            results.append("Теперь пользователю {} запрещено писать в репорт.".format(get_ref(i)))
            db.add_muted_report(i)
        else:
            results.append("@id{} (Пользователю) уже запрещено писать в репорт.".format(i))
    for i in group_words(results, "", delimiter="\n"):
        sendmessage_chat(chat_id, i)

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
def delblack(chat_id, user_ids, **kwargs):
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
        for i in tables:
            if hasattr(i, "chat_id"):
                i.delete().where(getattr(i, "chat_id").not_in(chat_ids)).execute()
    func()
    sendmessage_chat(chat_id, "Сканирование завершено")

        
        

@enable_command_with_permission(2)
def akick(chat_id,**kwargs):
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

""""
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
"""