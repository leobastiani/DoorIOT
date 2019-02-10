#!python2
#encoding=utf-8
from __future__ import print_function, division, absolute_import


from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, join_room, emit
import sys
from datetime import datetime, timedelta
from threading import Timer
from gpiozero import LED

USERS = {
    'user': '123',
}

DEBUG = False
def debug(*args):
    '''funciona como print, mas só é executada se sys.flags.debug == 1'''
    if not DEBUG:
        return ;
    print(*args)

# initialize Flask
app = Flask(__name__)
app.secret_key = 'secret key'
socketio = SocketIO(app)
KEY = 'secret key 2'
timer = None
MAXTIMEOPEN = 3 if not DEBUG else 10
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

def doLogin(login, password):
    if login in USERS:
        if USERS[login] == password:
            return True
    return False

@app.route('/')
def index():
    if datetime.now() <= LIBERADO:
        if KEY == request.args.get('key', ''):
            return render_template('door.html', websocket=True)
    return 'unauthorized'

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
        if doLogin(login, password):
            LIBERADO = datetime.now() + timedelta(hours=float(horas))
            msg = 'Sucesso!'
            link = '/?key='+KEY
        else:
            msg = 'Falha no login'
    return render_template('admin.html', liberado=LIBERADO.strftime("%Y-%m-%d %H:%M"),
        msg=msg, maxtimeopen=MAXTIMEOPEN, key=KEY, link=link, userValue=userValue, passValue=passValue)

@socketio.on('door')
def on_door(data):
    debug("data:", data)
    abrir = data.get('open', False)
    fechar = data.get('close', False)
    if abrir and not fechar:
        openDoor()
    elif fechar:
        closeDoor()

@socketio.on('connect')
def on_connect():
    debug('Connected!')

@socketio.on('disconnect')
def on_disconnect():
    debug('Disconnected!')

if __name__ == '__main__':
    socketio.run(app, debug=DEBUG, host='0.0.0.0')
