#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

from flask import Flask, redirect, url_for, render_template, session, request
from flask_socketio import emit, SocketIO
from tinydb import TinyDB, Query
import argparse
import os


STATE={
    'date':False,
    'hour':False,
    'place': False
}


# Carga aplicación Flask
app = Flask(__name__)

# Habilita sockets in aplicación Flaks
socketio = SocketIO(app)

# Carga base de datos de conversaciones
db = TinyDB('conversations.json')
Usuario= Query()

# Página principa.
@app.route('/')
def login():
  return render_template('home.html')

# Paǵina acerca de
@app.route('/about')
def about():
  return render_template('about.html')

# Página para agenda
@app.route('/calendar')
def calendar():
  username=request.args['username']
  if not len(username)>0:
      username='desconocido'
  user=db.search(Usuario.user == username)
  if len(user)==0:
      user=db.insert({'user':username,'conversations':[[]],'events':[]})
      user=db.get(eid=user)
  else:
      user=user[0]
  events=user['events']
  return render_template('agenda.html',username=username, user['events'])


# Página con chat
@app.route('/chat')
def chat():
  username=request.args['username']
  if not len(username)>0:
      username='desconocido'
  user=db.search(Usuario.user == username)
  if len(user)==0:
      user=db.insert({'user':username,'conversations':[[]],'events':[]})
      user=db.get(eid=user)
  else:
      user=user[0]
      events=user['events']
      conv=user['conversations']
      conv.append([])
      db.update({'conversations':conv,'events':events},eids=[user.eid])

  return render_template('chat.html',username=username)

# Mensajes con chat
@socketio.on('message', namespace='/ask')
def receive_message(message):
    username,message_=message['data'].split(':',1)
    user=db.search(Usuario.user == username)
    if len(user)==0:
      user=db.insert({'user':username,'conversations':[[]],'events':[]})
      user=db.get(eid=user)
    else:
      user=user[0]
    
    # REVISAR ESTADO
    if not STATE['date']:
        ans="¿Cúando?"
    elif not STATE['hour']:
        ans="¿A qué hora?"
    elif not STATE['place']:
        ans="¿Dónde?"
    else:
        ans="No entendí"
    events=user['events']
    conv=user['conversations']
    conv[-1].append({'msg':message_,'ans':ans})
    db.update({'conversations':conv,'events':events},eids=[user.eid])
    emit('response', {'data': ans.lower()})


# Función principal (interfaz con línea de comandos)
if __name__ == '__main__':
    p = argparse.ArgumentParser("pyAIML")
    p.add_argument("--host",default="127.0.0.1",
            action="store", dest="host",
            help="Root url [127.0.0.1]")
    p.add_argument("--port",default=5000,type=int,
            action="store", dest="port",
            help="Port url [500]")
    p.add_argument("--debug",default=False,
            action="store_true", dest="debug",
            help="Use debug deployment [Flase]")
    p.add_argument("-v", "--verbose",
            action="store_true", dest="verbose",
            help="Verbose mode [Off]")

    opts = p.parse_args()

    socketio.run(app,
	    debug=opts.debug,
            host=opts.host,
            port=opts.port)
