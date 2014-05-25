#!/usr/bin/python
import os
import re
import struct
import tornado.web
import tornado.ioloop
import tornado.template
import sqlite3
import random
from tornado import escape
from pprint import pprint

current_dir = os.path.dirname(os.path.realpath(__file__))
template_dir = "templates"
template_file = "admin.htm.template"

db_file = "codeclub.db3"

class Utils:
    valid_fullname = re.compile(r"^[A-Za-z]+(?: ?[A-Za-z]+)*$")
    valid_username = re.compile(r"^[a-z]+$")
    
    @staticmethod
    def string_cap(s, l):
        return s if len(s)<=l else s[0:l-3]+'...'
    
    @staticmethod
    def FullnameToUsername(fullname):
        fullname = fullname.lower()
        fullname = ''.join(fullname.split()) # Kill whitespace
        fullname = Utils.string_cap(fullname, 30)
        if Utils.valid_username.match(fullname):
            return fullname
        else:
            return False
    
    @staticmethod
    def CreatePassword():
        zoo_animals = ['elephant', 'lion', 'tiger', 'giraffe', 'penguin', 'gorillas', 'sharks',
            'panda', 'meerkat', 'crocodile', 'bear', 'otter', 'wolf', 'cheetah', 'snake', 'zebra',
            'frog', 'dolphin']
        fruits = ['strawberry', 'mango', 'watermelon', 'banana', 'orange', 'apple', 'grape',
            'peach', 'cherry', 'raspberry', 'kiwi', 'blueberry', 'lemon', 'pear', 'plum',
            'blackberry', 'lime']
        number = ord(struct.unpack("<c", os.urandom(1))[0])
        return random.choice(fruits) + random.choice(zoo_animals) + str(number)
        

class AdminHandler(tornado.web.RequestHandler):
    def get(self):
        c = db.query("SELECT fullname, username, password, url, indexed FROM students")
        students = []
        for record in c.fetchall():
            students.append({
                'fullname': record[0],
                'username': record[1],
                'password': record[2],
                'url': record[3],
                'isindexed': record[4],
                'deletelink': 'http://code.club:8080/del/' + record[1],
            })
        template_loader = tornado.template.Loader(current_dir + "/" + template_dir)
        
        output_html = template_loader.load(template_file).generate(students=students)
        self.write(output_html)
    def post(self):
        fullname = escape.xhtml_escape(self.get_argument('fullname'))
        username = escape.xhtml_escape(self.get_argument('username'))
        password = self.get_argument('password')
        url = escape.xhtml_escape(self.get_argument('url'))
        try:
            indexed = True if self.get_argument('indexed') == "on" else False
        except tornado.web.MissingArgumentError:
            indexed = False
        
        if not fullname:
            self.write("Full Name must be specified")
            return
        elif not Utils.valid_fullname.match(fullname):
            self.write("Full Name must just be letters with a single space separating the names")
            return

        if not username:
            username = Utils.FullnameToUsername(fullname)
            if not username:
                self.write("Please specify a username, I couldn't create one from %s" % fullname)
                return
        if not password:
            password = Utils.CreatePassword()
        if not url:
            url = username + ".code.club"
        
        self.write( "%s %s %s %s %r" % (fullname, username, password, url, indexed))
        

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Index")
        
application = tornado.web.Application([
    (r"/", IndexHandler),
    (r"/admin.htm", AdminHandler),
], debug=True)

class DatabaseHandler(object):
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.cur = self.conn.cursor()

    def query(self, arg):
        self.cur.execute(arg)
        self.conn.commit()
        return self.cur

    def __del__(self):
        self.conn.close()

if __name__ == "__main__":
    application.listen(8080)
    db = DatabaseHandler(current_dir + "/" + db_file)
    db.query('''CREATE TABLE IF NOT EXISTS students 
            (fullname TEXT, username TEXT UNIQUE, password TEXT, url TEXT, indexed INT)''')
    tornado.ioloop.IOLoop.instance().start()