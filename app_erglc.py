#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

from flask import Flask, redirect, url_for, render_template, session, request
from flask_socketio import emit, SocketIO
from tinydb import TinyDB, Query
import argparse
import os
import re
import nltk

# Carga aplicación Flask
app = Flask(__name__)

# Habilita sockets in aplicación Flaks
socketio = SocketIO(app)

# Carga base de datos de conversaciones
db = TinyDB('conversations.json')
Usuario= Query()

exp_regs=[
    (re.compile(r'hola'),'hola, cúal es tu nombre'),
    (re.compile(r'mi nombre es (.*)'),'mucho gusto {0}, a que equipo le vas'),
    (re.compile(r'me llamo (.*)'),'mucho gusto {0}'),
    (re.compile(r'.*america.*'),'fuchi, que haces'),
    (re.compile(r'.*pumas.*'),'no tal mal, que haces'),
    (re.compile(r'.*toluca.*'),'muy bien, que haces'),
    (re.compile(r'nada'),'como pez en el agua'),
    (re.compile(r'trabajando'),'en que trabajas'),
]

command_grammar = nltk.CFG.fromstring("""
    S -> VP
    PP -> P NP
    NP -> Det N | Det N PP 
    VP -> V NP | VP PP
    Det -> 'un' | 'una'
    N -> 'dicho' | 'broma'
    V -> 'di'
    P -> 'sobre'
""")


parser = nltk.ChartParser(command_grammar)


# Página principa.
@app.route('/')
def login():
  return render_template('home.html')

# Paǵina acerca de
@app.route('/about')
def about():
  return render_template('about.html')


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
    
   
    ans=None
    for exp_reg,ans_template in exp_regs:
        m=exp_reg.match(message_)
        if m:
            ans=ans_template.format(*m.groups())
            break
    if not ans:
        sent = message_.split()
        trees=parser.parse(sent)
        for tree in trees:
            print(tree)
            for sub in tree.subtrees(filter=lambda x: x.label() == 'VP'):
                if sub[0].label()=="V" and sub[0][0]=="di":
                    topic=sub[1][1][0]
            break
        
        if topic=='dicho':
            ans="agua pasa por mi casa"
        elif topic=="broma": 
            ans="mi hijo se siente pez en el agua\nqué hace\nnada"
                


    if not ans:
        ans="podrías repetirlo"

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
