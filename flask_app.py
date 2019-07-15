#!/usr/bin/python3
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, jsonify, request, send_from_directory
from peewee import *
from playhouse.shortcuts import model_to_dict
from playhouse.flask_utils import PaginatedQuery
import sqlite3
import datetime
from peewee import *
from flask_cors import CORS
from vk_api import VkApi
from vk_api.bot_longpoll import CHAT_START_ID
import os
import module
from module_to_flask import *
from base64 import b64encode
from collections import OrderedDict
from hashlib import sha256
from hmac import HMAC
from urllib.parse import urlparse, parse_qsl, urlencode
from utils import *
from functools import wraps
import requests
import chats_urls
from openpyxl import Workbook

app = Flask(__name__)
app.register_blueprint(chats_urls.bp, url_prefix="/chats/<int:chat_id>")
CORS(app)


def is_valid(*, query: dict, secret: str) -> bool:
    """Check VK Apps signature"""
    vk_subset = OrderedDict(sorted(x for x in query.items() if x[0][:3] == "vk_"))
    hash_code = b64encode(HMAC(secret.encode(), urlencode(vk_subset, doseq=True).encode(), sha256).digest())
    decoded_hash_code = hash_code.decode('utf-8')[:-1].replace('+', '-').replace('/', '_')
    return query["sign"] == decoded_hash_code


def auth_wrap(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        url = "https://example.com/?" + "&".join([f"{k}={v}" for k, v in request.args.items()])
        query_params = dict(parse_qsl(urlparse(url).query, keep_blank_values=True))
        status = is_valid(query=query_params, secret=client_secret)

        if not status:
            return jsonify(items="error: Not permission")
        if "from_id" in f.__code__.co_varnames:
            return f(from_id=request.args.get("vk_user_id"), *args, **kwargs)
        return f(*args, **kwargs)
    return wrapper


def check_helper_wrap(f):
    @wraps(f)
    def wrap(from_id, *args, **kwargs):
        try:
            Helpers.get(user_id=from_id)
            kwargs["from_id"] = from_id
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify(items=False)
    return wrap


def convert(models, exclude=[]):
    for i in models:
        try:
            yield model_to_dict(i, backrefs=True, exclude=exclude)
        except:
            continue


@app.route("/generate_doc")
def generate_file_doc():
    wb = Workbook()
    ws = wb.active
    ws.append(["Маты"])
    for i in module.CurseWords.select():
        ws.append([i.word])
    wb.save("./uploads/test.xlsx")
    return "Success"


@app.route('/ans_report/<int:rep_id>/<path:text>')
@auth_wrap
@check_helper_wrap
def add_report(text=None, from_id=None, rep_id=None):
    helper = module.Helpers.get(user_id=from_id)
    rep = module.Reports.get_by_id(rep_id)
    rep.otext = text
    rep.helper = str(from_id)
    rep.otime = module.get_time()
    rep.save()
    service_session = VkApi(token=service_token)
    service_api = service_session.get_api()
    service_api.notifications.sendMessage(user_ids=rep.user_id, message=f"Агент поддержки #{helper.id} ответил на вопрос {rep.id}", fragment=f"report{rep.id}")
    return jsonify(items="Success")


@app.route("/")
def teste():
    return "Сайт TheDeaX"


@app.route('/cleaner/')
@auth_wrap
def clean_world(from_id=None):
    return f"{str(module.Users.delete().where(module.Users.message_year < 50).execute())} users cleaned"


@app.route('/admins/')
@auth_wrap
def admins_get(chat_id=None, user_id=None, from_id=None):
    data = {"items": []}
    query = Admin_List.select()
    for admin in query.dicts():
        data["items"].append(admin)
    return jsonify(data)


@app.route('/adminses/')
@auth_wrap
def adminses_get(chat_id=None, user_id=None, from_id=None):
    data = {"items": []}
    t = dict(**request.args)
    if "page" in t:
        del t["page"]
    query = Admin_List.filter(**t) if t else Admin_List.select()
    pg = PaginatedQuery(query, 20)
    for admin in convert(pg.get_object_list()):
        data["items"].append(admin)
    return jsonify(data)


@app.route('/helpers/')
@app.route('/helpers/<int:user_id>/')
@auth_wrap
# @check_helper_wrap
def get_helpers_list(user_id=None, from_id=None):
    data = {"items": []}
    query = module.Helpers.select(module.Helpers.avatar, module.Helpers.vig, module.Helpers.admin, module.Helpers.reports, module.Helpers.data, module.Helpers.id)
    if user_id:
        query = query.where(module.Helpers.user_id == user_id)
    for helpers in query.dicts():
        data["items"].append(helpers)
    return jsonify(data)


@app.route('/check_helper/')
@auth_wrap
@check_helper_wrap
def check_helper(from_id=None):
    try:
        return jsonify(items=model_to_dict(Helpers.get(user_id=from_id)))
    except:
        return jsonify(items=False)


@app.route('/methods/users_get')
def get_vk_users():
    user_ids = request.args.get("user_ids")
    return jsonify(items=vk.users.get(user_ids=user_ids, fields="photo_100"))


@app.route('/methods/groups_is_member/<int:group_id>')
@auth_wrap
def groups_is_member(group_id=None, from_id=None):
    return jsonify(bool(vk.groups.isMember(group_id=group_id, user_id=from_id)["member"]))


@app.route('/checkblack/')
@auth_wrap
def check_blacklist(from_id=None):
    try:
        module.Black_List.get(user_id=from_id)
        return jsonify(items=True)
    except:
        return jsonify(items=False)


@app.route('/reports/')
@app.route('/reports/<int:id>/')
@auth_wrap
def get_reports_list(id=None):
    data = {"items": []}
    query = module.Reports.select()
    if id:
        query = query.where(module.Reports.id == id)
    for report in query.dicts():
        data["items"].append(report)
    return jsonify(data)


@app.route('/report_create/<path:text>')
@auth_wrap
def create_report(from_id=None, text=""):
    r = db.add_report(from_id, -1, text)
    sendmessage_chat(2, f"Пришёл новый репорт из сервиса: https://vk.com/worldbots#support{secret_key}-report{r.id}")
    return jsonify(items=r.id)


@app.route('/service/')
@app.route('/service/<int:user_id>/')
@auth_wrap
def get_service(user_id=None):
    data = {"items": []}
    query = Service.select()
    if user_id:
        query = query.where(Service.user_id == user_id)
    for user in query.dicts():
        data["items"].append(user)
    return jsonify(data)


@app.route('/chats/')
@app.route('/chats/<int:chat_id>/')
@auth_wrap
def get_chats(chat_id=None, from_id=None):
    data = {"items": []}
    chats = list(map(lambda x: x.chat_id, Admin_List.select().where(Admin_List.user_id == from_id)))
    query = Chat_Info.select().where(Chat_Info.chat_id.in_(chats))
    if chat_id:
        query = query.where(Chat_Info.chat_id == chat_id)
    for chat in query.dicts():
        data["items"].append(chat)
    return jsonify(data)


@app.route('/banlist/')
@app.route('/banlist/<int:chat_id>/')
@auth_wrap
def get_ban_list(chat_id=None):
    data = {"items": []}
    query = module.Ban_List.select().where(module.Ban_List.user_id > 0)
    if chat_id:
        query = query.where(module.Ban_List.chat_id == chat_id)
    for user in query.dicts():
        data["items"].append(user)
    data["response"] = ",".join(map(str, [i.user_id for i in query]))
    return jsonify(data)


@app.route('/chat_users/<int:chat_id>/')
@auth_wrap
def get_chat_users(chat_id=None, from_id=None):
    data = {"items": []}
    if db.get_level_admin(chat_id, from_id) == 0:
        return jsonify("You not have permission to this chat")
    try:
        r = vk.messages.getConversationMembers(peer_id=CHAT_START_ID + chat_id)["profiles"]
        for i in r:
            lvl = db.get_level_admin(chat_id, i["id"])
            i["level"] = lvl
            data["items"].append(i)
        return jsonify(data)
    except Exception as e:
        return jsonify(error=str(e))


@app.route('/users/')
@auth_wrap
def get_users():
    data = {"items": []}
    for user in module.Users.select().where().dicts():
        data["items"].append(user)
    return jsonify(data)


@app.route('/service/add/')
@auth_wrap
def add_service(from_id=None):
    data = {"items": []}
    try:
        db.add_service(from_id)
        data["items"].append({
            "success": "1"
        })
    except Exception as e:
        data["items"].append({
            "error": str(e)
        })
    return jsonify(data)


@app.route("/add_story/")
def add_story():
    try:
        upload_url = request.args.get("upload_url")
        request_result = requests.post(upload_url, files={'file': open("story.png", "rb")})
    except Exception as e:
        return str(e)
    return "Success"
#app.run(host="0.0.0.0", port=8000, ssl_context=("/etc/letsencrypt/csr/0002_csr-certbot.pem", "/etc/letsencrypt/keys/0002_key-certbot.pem"))
