from flask import *
from .config import *
import json
import pymysql
import requests
import urllib.parse
from _thread import start_new_thread
from threading import Thread
import pymorphy2
from pytils import translit

db = pymysql.connect(MYSQL_SERVERNAME,
                     MYSQL_USERNAME,
                     MYSQL_PASSWORD,
                     MYSQL_DBNAME,
                     charset='utf8')

headers = {'content-type': 'application/x-www-form-urlencoded'}

analyzer = pymorphy2.MorphAnalyzer()

akadoton = Blueprint('akadoton', __name__, template_folder='templates', static_folder='static')

commands = (
    {
        'voice_commands': ('включи', 'включить', 'зажги'),
        'zway_command': 'on',
        'replay': 'Включила %s'
    },
    {
        'voice_commands': ('выключи', 'выключить', 'погаси', 'погасить'),
        'zway_command': 'off',
        'replay': 'Выключила %s'
    },
    {
        'voice_commands': ('открой', 'отопри', 'дверь мне запили'),
        'zway_command': 'open',
        'replay': 'Открыла %s'
    },
    {
        'voice_commands': ('закрой', 'запри'),
        'zway_command': 'close',
        'replay': 'Закрыла %s'
    },
    {
        'voice_commands': (
            'покажи устройства', 'выведи список устройств', 'покажи список устройств', 'выведи устройства',
            'устройства в доме', 'список устройств'
        ),
        'zway_command': 'list',
        'replay': 'Вот список устройств, которые я знаю: %s,'
                  ' Пользовательские устройства: %s'
    },
    {
        'voice_commands': (
            'состояние', 'покажи состояние', 'скажи состояние', 'в каком состоянии', 'включен ли', 'выключен ли',
            'горит ли', 'открыта ли', 'закрыта ли', 'заперта ли'
        ),
        'zway_command': 'get',
        'replay': '%s %s'
    },
    {
        'voice_commands': ('выбрать дом', 'выбери дом', 'переключить дом'),
        'zway_command': 'unpair_house',
        'replay': 'Дом отвязан'
    },
    {
        'voice_commands': ('отвязать дом', 'отвяжи дом', 'отвязать контроллер', 'отвяжи контроллер'),
        'zway_command': 'switch_house',
        'replay': 'Переключилась в дом %s'
    },
    {
        'voice_commands': ('обнови список устройств', 'обновить список устройств'),
        'zway_command': 'update_devices_list',
        'replay': 'Готово'
    },
    {
        'voice_commands': ('помощь',),
        'zway_command': 'help',
        'replay': 'Для управления светом используй слова «Включи» или «Выключи» и имя устройства ровно так,'
                  ' как оно названо в контроллере. Для управления замком используй команды «Открой» и «Закрой».'
                  ' Для просмотра списка устройства скажи «Покажи список устройств».'
                  ' Для отключения контроллера скажи «Отвязать дом»'
    },
    {
        'voice_commands': ('пользовательские устройства',),
        'zway_command': 'user_list',
        'replay': 'Список устройств, подключенных вручную: '
    },
    {
        'voice_commands': ('добавить устройство', 'добавить'),
        'zway_command': 'add',
        'replay': 'Устройство %s добавлено. Ваш пользовательский индификатор %s. Индификатор устройства %s'
    },
    {
        'voice_commands': ('проверить выполнение',),
        'zway_command': 'check_exc',
        'replay': 'Устройство %s добавлено. Ваш пользовательский индификатор %s. Индификатор устройства %s'
    },
)


class CommandExecute(Thread):

    def __init__(self, func, args):

        self.func = func
        self.args = args
        self.status = 0
        self.result = None
        self.exc = None

        super().__init__(target=self.run)
        self.start()

    def run(self):
        try:
            result = self.func(self.args)
            if json.loads(result)['code'] == 200:
                self.result = 'Команда выполнена'
                self.status = 1
            else:
                self.exc = result
                self.status = 2
        except Exception as ex:
            self.status = 2
            self.exc = ex

    def get_result(self):
        if self.status == 1:
            return self.result
        if self.status == 2:
            return self.exc
        return 'Not ready yet'


class User:
    def __init__(self, user_id, home_id, remote_id, login, password, session_1, session_2, state, _):
        self.login = login
        self.password = password
        self.id = user_id
        self.home_id = home_id
        self.state = state
        self.remote_id = remote_id
        self.session = {'ZBW_SESSID': session_1, 'ZWAYSession': session_2}
        start_new_thread(self.update_devices, ())

    def auth(self):
        url = urllib.parse.urljoin(FIND_SERVER, '/zboxweb')
        resp = requests.post(url, data='act=login&login=%s/%s&pass=%s' % (self.remote_id, self.login, self.password),
                             allow_redirects=False, headers=headers)
        print('Auth....')
        cookies = resp.cookies.get_dict()
        print(cookies)
        if not cookies.get('ZBW_SESSID') or not cookies.get('ZWAYSession'):
            return False
        sql_execute('''
        UPDATE user_homes SET ZBW_SESSID='%s', ZWAYSession='%s' WHERE home_id=%s AND user_id='%s' AND remote_id=%s
        ''' % (cookies["ZBW_SESSID"], cookies["ZWAYSession"], self.home_id, self.id, self.remote_id))
        self.session = cookies
        return True

    def request(self, cmd):
        url = urllib.parse.urljoin(FIND_SERVER, '/ZAutomation/api/v1/devices' + cmd)
        print(url, self.session)
        return requests.get(url, cookies=self.session)

    def update_custom_device(self, cmd):
        pass

    def send_request(self, cmd):
        if not self.session:
            if not self.auth():
                return False
        resp = self.request(cmd)
        if cmd:
            print(resp.text)
        if resp.status_code != 403 and resp.status_code != 307:
            return resp.text
        if self.auth():
            resp = self.request(cmd)
            return resp.text
        return ''

    def update_devices(self):
        resp = self.send_request('')
        if not resp:
            return False
        resp = json.loads(resp)
        if not resp.get('data') or not resp['data'].get('devices'):
            return False

        devices = [
            "(0, %s, '%s', '%s')" % (
                self.home_id,
                device['id'],
                device['metrics']['title']
            )
            for device in resp['data']['devices'] if not device['permanently_hidden']
        ]

        devices_list = ','.join(devices)
        sql_execute("DELETE FROM home_devices WHERE home_id=%s" % self.home_id)
        sql_execute("INSERT INTO home_devices VALUES %s" % devices_list)
        sql_execute("UPDATE user_homes SET update_time=NOW() WHERE home_id=%s AND user_id='%s'" % (
            self.home_id,
            self.id
        ))
        return True

    def find_device(self, device_name):
        return sql_get("SELECT device_id, device_name FROM home_devices"
                       " WHERE home_id=%s AND LOWER(device_name) = LOWER('%s') LIMIT 1" % (self.home_id, device_name))

    def get_devices(self):
        return sql_get("SELECT device_id, device_name FROM home_devices WHERE home_id=%s" % self.home_id)

    def get_custom_devices(self):
        return sql_get(
            "SELECT name, state FROM custom_devices WHERE user_id = '%s'" % self.id[len(self.id) - 4:])


session = None
version = None


def get_reply(text, buttons=(), tts=None, end_session=False):
    if not tts:
        tts = text
    resp = {
        'response': {
            'text': text,
            'tts': tts,
            'buttons': buttons,
            'end_session': end_session
        },
        'session': session,
        'version': version
    }
    return json.dumps(resp)


def sql_execute(sql):
    db.ping()
    with db.cursor() as cursor:
        cursor.execute(sql + ';')
    db.commit()


def sql_get(sql):
    db.ping()
    with db.cursor() as cursor:
        cursor.execute(sql + ';')
        result = cursor.fetchall()
    return result


def normal(s):
    lst = s.split(' ')
    return ' '.join([analyzer.normal_forms(i)[0] for i in lst])


reqs = {}


@akadoton.route('/', methods=['POST'])
def main():
    global version, session

    session = request.json['session']
    version = request.json['version']

    user_id = request.json['session']['user_id']
    command = request.json['request']['command']
    original_command = request.json['request']['original_utterance']

    result = sql_get(
        "SELECT home_id, remote_id, username, password, ZBW_SESSID, ZWAYSession, state, (update_time < NOW() +"
        " INTERVAL 10 MINUTE) AS outdated FROM user_homes WHERE user_id = '%s'" % user_id)

    if not result:
        print('NEW USER %s' % user_id)
        sql_execute(
            "INSERT INTO user_homes VALUES (default, '%s', 0, '', '', '', '', 'Дом', 0, NOW(), FALSE)" % user_id)
        return get_reply(TEXT_REGISTER_NEW)
    user = User(user_id, *(result[0]))
    print(result)

    if user.state == HOME_STATE_NEW:
        try:
            remote_id = int(command)
        except ValueError:
            return get_reply('Только цифры! ')
        sql_execute("UPDATE user_homes SET remote_id='%s', state=%s WHERE home_id=%s AND user_id='%s'" % (
            remote_id, HOME_STATE_REMOTEID, user.home_id, user.id))
        user.remote_id = remote_id
        user.state = HOME_STATE_REMOTEID
        return get_reply(TEXT_REGISTER_USERNAME)

    if user.state == HOME_STATE_REMOTEID:
        command = original_command
        if not command:
            return get_reply(TEXT_REGISTER_USERNAME_REPEAT)

        user.login = command
        user.state = HOME_STATE_REMOTEID_USERNAME
        sql_execute("UPDATE user_homes SET username='%s', state=%s WHERE home_id=%s AND user_id='%s'" % (
            command, HOME_STATE_REMOTEID_USERNAME, user.home_id, user.id))
        return get_reply(TEXT_REGISTER_PASSWORD)

    if user.state == HOME_STATE_REMOTEID_USERNAME:
        command = original_command
        if not command:
            return get_reply(TEXT_REGISTER_PASSWORD_REPEAT)

        user.password = command
        user.state = HOME_STATE_REMOTEID_USERNAME_PASSWORD

        sql_execute("UPDATE user_homes SET password='%s', state=%s WHERE home_id=%s AND user_id='%s'" % (
            command, HOME_STATE_REMOTEID_USERNAME_PASSWORD, user.home_id, user.id))

    if user.state == HOME_STATE_REMOTEID_USERNAME_PASSWORD:
        if user.auth():
            sql_execute("UPDATE user_homes SET state=%s WHERE home_id=%s AND user_id='%s'" % (
                HOME_STATE_READY, user.home_id, user.id))
            user.state = HOME_STATE_READY
            return get_reply(TEXT_REGISTER_READY)
        sql_execute("UPDATE user_homes SET state=%s WHERE home_id=%s AND user_id='%s'" % (
            HOME_STATE_NEW, user.home_id, user.id))
        user.state = HOME_STATE_NEW
        return get_reply(TEXT_REGISTER_FAILED)

    if user.state == HOME_STATE_READY:
        print(command)

        for cmd in commands:
            for c in cmd['voice_commands']:
                c = normal(c)
                if c in normal(command):
                    match_command = cmd
                    sl = len(c.split())
                    target = ' '.join(command.split()[sl:])
                    break
            else:
                continue
            break
        else:
            return get_reply('Неизвестная команда')

        command = match_command['zway_command']
        replay = match_command['replay']

        if command == 'help':
            return get_reply(replay)

        if command == 'list':
            lst = [device[1] for device in user.get_devices()]
            custom_lst = [device[0] for device in user.get_custom_devices()]
            return get_reply(replay % (', '.join(lst), ', '.join(custom_lst)))

        if command in ['on', 'off', 'open', 'close']:
            device = user.find_device(target)
            print(device)
            if not device:
                return get_reply('Устройство %s не найдено' % target)
            reqs[user.id] = CommandExecute(user.send_request, ('/%s/command/%s' % (device[0][0], command)))
            return get_reply(replay % target, buttons=[
                {
                    "title": "Проверить выполнение",
                    "hide": True
                }
            ])

        if command == 'check_exc':
            if reqs.get(user.id):
                return get_reply(str(reqs[user.id].get_result()))
