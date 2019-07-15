from flask import Blueprint, request, jsonify, g
from functools import wraps
from base64 import b64encode
from collections import OrderedDict
from hashlib import sha256
from hmac import HMAC
from urllib.parse import urlparse, parse_qsl, urlencode
from utils import *
import module


def is_valid(*, query: dict, secret: str) -> bool:
    """Check VK Apps signature"""
    vk_subset = OrderedDict(sorted(x for x in query.items() if x[0][:3] == "vk_"))
    hash_code = b64encode(HMAC(secret.encode(), urlencode(vk_subset, doseq=True).encode(), sha256).digest())
    decoded_hash_code = hash_code.decode('utf-8')[:-1].replace('+', '-').replace('/', '_')
    return query["sign"] == decoded_hash_code


def auth_wrap(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        """
        try:
            status = is_valid(query="&".join([f"{k}={v}" for k, v in request.args.items()]), secret="T0KjbYYFEB5VlbUh3ACv")
            print(status)
        except Exception as e:
            status = False
        if not status:
            return jsonify(items="error: No access")
        """
        url = "https://example.com/?" + "&".join([f"{k}={v}" for k, v in request.args.items()])
        query_params = dict(parse_qsl(urlparse(url).query, keep_blank_values=True))
        status = is_valid(query=query_params, secret=client_secret)

        if not status:
            return jsonify(items="error: Not permission")
        if "from_id" in f.__code__.co_varnames:
            return f(from_id=request.args.get("vk_user_id"), *args, **kwargs)
        return f(*args, **kwargs)
    return wrapper


bp = Blueprint("chats", __name__, url_prefix="/chats/<int:chat_id>")


@bp.url_value_preprocessor
@auth_wrap
def verify_chat(endpoint, values, from_id):
    chat_id = values.get("chat_id")
    values["from_id"] = from_id
    g.from_id = from_id
    g.chat_id = chat_id


@bp.before_request
def verify_chat1():
    from_id = g.from_id
    chat_id = g.chat_id
    try:
        module.Chat_Info.get(chat_id=chat_id)
    except Exception as e:
        return jsonify(error=f"Chat not exists!")
    try:
        module.Admin_List.get(chat_id=chat_id, user_id=from_id)
    except:
        return jsonify(error="You not have permission to this chat")


@bp.route('/addadm/')
def chat_addadm(chat_id=None, from_id=None):
    data = {"items": []}
    user_ids = request.args.get("user_ids")
    if not user_ids:
        return jsonify(error="Parametr user_ids is not found!")
    user_ids = filter(lambda x: x > 0, map(int, user_ids.split(",")))
    if db.get_level_admin(chat_id, from_id) < 3:
        return jsonify(items=dict(error="not permission"))
    for i in user_ids:
        if db.get_level_admin(chat_id, from_id) <= db.get_level_admin(chat_id, i):
            data["items"].append({
                "error": "not have permission"
            })
            continue
        try:
            db.add_admin(chat_id, i, 2)
            data["items"].append({
                "success": "1"
            })
        except Exception as e:
            data["items"].append({
                "error": str(e)
            })
            continue
    return jsonify(data)


@bp.route('/rename_title/<path:title>/')
def rename_chat_title(chat_id=None, from_id=None, title=None):
    data = {'items': []}
    if db.get_level_admin(chat_id, from_id) == 0:
        data["items"].append({
            "error": "Not permission"})
        return jsonify(data)
    chat = module.Chat_Info.get(chat_id=chat_id)
    chat.title = title
    chat.save()
    vk.messages.editChat(chat_id=chat_id, title=title)
    r = get_ref(from_id)
    sendmessage_chat(chat_id, f"{r} изменил название конференции на '{title}'")
    data["items"].append("success")
    return jsonify(data)


@bp.route('/kick/')
def chat_kick(chat_id=None, from_id=None):
    data = {"items": []}
    if db.get_level_admin(chat_id, from_id) == 0:
        return jsonify(error="error: not permission")
    user_ids = request.args.get("user_ids")
    if not user_ids:
        return jsonify(error="Parametr user_ids is not found!")
    user_ids = filter(lambda x: x > 0, map(int, user_ids.split(",")))
    for i in user_ids:
        if db.get_level_admin(chat_id, from_id) <= db.get_level_admin(chat_id, i):
            data["items"].append({
                "error": "not have permission"
            })
            continue
        try:
            vk.messages.removeChatUser(chat_id=chat_id, member_id=i)
            x1 = get_ref(from_id)
            x2 = get_ref(i, name_case="gen")
            sendmessage_chat(chat_id, f"{x1} исключил {x2}")
            try:
                module.Admin_List.get(chat_id=chat_id, user_id=i).delete_instance()
            except Exception as e:
                print(e)
            data["items"].append({
                "success": "1"
            })
        except Exception as e:
            data["items"].append({
                "error": str(e)
            })
            continue
    return jsonify(data)


@bp.route('/check_update/')
def chat_check_update(chat_id=None, from_id=None):
    r = vk.messages.getConversationsById(peer_ids=CHAT_START_ID + chat_id)["items"][0]
    settings = r["chat_settings"]
    chat_id_info = r["peer"]["id"]
    title = settings["title"]
    photo = settings["photo"]["photo_200"] if "photo" in settings else "."
    chat = Chat_Info.get_or_create(chat_id=chat_id)[0]
    chat.title = title
    chat.photo = photo
    chat.save()
    return jsonify(response=True)


@bp.route('/ban/')
def chat_ban(chat_id=None, from_id=None):
    data = {"items": []}
    if db.get_level_admin(chat_id, from_id) < 2:
        return jsonify(items="error: not permission")
    user_ids = request.args.get("user_ids")
    if not user_ids:
        return jsonify(error="Parametr user_ids is not found!")
    user_ids = filter(lambda x: x > 0, map(int, user_ids.split(",")))
    for i in user_ids:
        if db.get_level_admin(chat_id, from_id) <= db.get_level_admin(chat_id, i):
            data["items"].append({
                "error": "not have permission"
            })
            continue
        try:
            try:
                vk.messages.removeChatUser(chat_id=chat_id, member_id=i)
            except:
                ...
            try:
                module.Admin_List.get(chat_id=chat_id, user_id=i).delete_instance()
            except Exception as e:
                print(e)
            try:
                db.add_ban(chat_id, i)
                x1 = get_ref(from_id)
                x2 = get_ref(i, name_case="gen")
                sendmessage_chat(chat_id, f"{x1} заблокировал {x2}")
                data["items"].append({
                    "success": "1"
                })
            except Exception as e:
                data["items"].append({
                    "error": e
                })
        except Exception as e:
            data["items"].append({
                "error": str(e)
            })
            continue
    return jsonify(data)


@bp.route('/unban/')
def chat_unban(chat_id=None, from_id=None):
    data = {"items": []}
    if db.get_level_admin(chat_id, from_id) == 0:
        return jsonify(error="error: not permission")
    user_ids = request.args.get("user_ids")
    if not user_ids:
        return jsonify(error="Parametr user_ids is not found!")
    user_ids = filter(lambda x: x > 0, map(int, user_ids.split(",")))
    for i in user_ids:
        db.remove_ban(chat_id, i)
    return jsonify(data)


@bp.route('/deladmin/')
def chat_deladmin(chat_id=None, from_id=None):
    data = {"items": []}
    if db.get_level_admin(chat_id, from_id) == 0:
        return jsonify(error="error: not permission")
    user_ids = request.args.get("user_ids")
    if not user_ids:
        return jsonify(error="Parametr user_ids is not found!")
    user_ids = filter(lambda x: x > 0, map(int, user_ids.split(",")))
    for i in user_ids:
        if db.get_level_admin(chat_id, from_id) <= db.get_level_admin(chat_id, i):
            data["items"].append({
                "error": "not have permission"
            })
            continue
        try:
            db.remove_admin(chat_id, i)
            data["items"].append({
                "success": "1"
            })
        except Exception as e:
            data["items"].append({
                "error": str(e)
            })
            continue
    return jsonify(data)


@bp.route('/setakick/<int:akick>/')
def chat_setakick(chat_id=None, from_id=None, akick=None):
    data = {"items": []}
    if db.get_level_admin(chat_id, from_id) == 0:
        return jsonify(error="error: not permission")
    try:
        db.set_akick(chat_id, akick)
        data["items"].append({
            "success": "1"
        })
    except Exception as e:
        data["items"].append({
            "error": str(e)
        })
        return
    return jsonify(data)


@bp.route('/addmoder/')
def chat_addmoder(chat_id=None, from_id=None):
    data = {"items": []}
    user_ids = request.args.get("user_ids")
    if not user_ids:
        return jsonify(error="Parametr user_ids is not found!")
    user_ids = filter(lambda x: x > 0, map(int, user_ids.split(",")))
    if db.get_level_admin(chat_id, from_id) < 3:
        return jsonify(items=dict(error="not permission"))
    for i in user_ids:
        if db.get_level_admin(chat_id, from_id) <= db.get_level_admin(chat_id, i):
            data["items"].append({
                "error": "not have permission"
            })
            continue
        try:
            db.add_admin(chat_id, i, 1)
            data["items"].append({
                "success": "1"
            })
        except Exception as e:
            data["items"].append({
                "error": str(e)
            })
            continue
    return jsonify(data)


@bp.route('/delchat/')
def chat_delchat(chat_id=None):
    data = {"items": None}
    try:
        r = vk.messages.getConversationsById(peer_ids=CHAT_START_ID + chat_id)["items"][0]
        return jsonify(error="Is not deleted!!!")
    except Exception as e:
        try:
            db.delete_chat(chat_id)
            module.Admin_List.delete().where(module.Admin_List.chat_id == chat_id).execute()
        except:
            ...
        data["items"] = "+"
        return jsonify(data)
