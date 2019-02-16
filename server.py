#!python2
#encoding=utf-8
from __future__ import print_function, division, absolute_import

from functools import wraps
from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, join_room, emit
import sys
from datetime import datetime, timedelta
from threading import Timer
from gpiozero import LED
from users import USERS

import argparse

parser = argparse.ArgumentParser(description='Open the door of my house')
parser.add_argument('--debug', '-d', action='store_true', help='Debug mode')
args = parser.parse_args()

DEBUG = args.debug

def debug(*args):
    '''funciona como print, mas só é executada se sys.flags.debug == 1'''
    if not DEBUG:
        return ;
    print(*args)

# initialize Flask
app = Flask(__name__)
KEY = 'first_key'
timer = None
MAXTIMEOPEN = 3
LIBERADO = datetime.now()
PORTA = LED(17)
# começa a porta em off
PORTA.off()
if DEBUG:
    LIBERADO += timedelta(hours=5)
    KEY = ''

def openDoor():
    global timer
    debug('Opening!')
    if timer is not None:
        timer.cancel()
    timer = Timer(MAXTIMEOPEN, closeDoor)
    timer.start()
    PORTA.on()

def closeDoor():
    global timer
    if timer is None:
        return
    debug('Closing!')
    timer.cancel()
    timer = None
    PORTA.off()

def canLogin(login, password):
    if login in USERS:
        if USERS[login] == password:
            return True
    return False

def withAuthorized(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if datetime.now() <= LIBERADO:
            if KEY == request.args.get('key', ''):
                return f(*args, **kwargs)
        return 'unauthorized'
    return decorated_function

@app.route('/')
@withAuthorized
def index():
    return render_template('door.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    global LIBERADO, KEY
    msg = False
    link = False
    # valores dos usuários para depurar
    userValue = USERS.keys()[0] if DEBUG else ''
    passValue = USERS[userValue] if DEBUG else ''
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        horas = request.form['horas']
        KEY = request.form['key']
        if canLogin(login, password):
            LIBERADO = datetime.now() + timedelta(hours=float(horas))
            msg = 'Sucesso!'
            link = '/?key='+KEY
        else:
            msg = 'Falha no login'
    return render_template('admin.html', liberado=LIBERADO.strftime("%Y-%m-%d %H:%M"),
        msg=msg, maxtimeopen=MAXTIMEOPEN, key=KEY, link=link, userValue=userValue, passValue=passValue)

@app.route('/door')
@withAuthorized
def door():
    abrir = request.args.get('open', False, type=int)
    fechar = request.args.get('close', False, type=int)
    if abrir and not fechar:
        openDoor()
    elif fechar:
        closeDoor()
    return ''

if __name__ == '__main__':
    app.run(debug=DEBUG, host='0.0.0.0')
