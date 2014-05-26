#!/usr/bin/python
import os
import re
import struct
import pwd
import tornado.web
import tornado.ioloop
import tornado.template
import sqlite3
import random
import subprocess
import lockfile
from tornado import escape
from pprint import pprint

current_dir = os.path.dirname(os.path.realpath(__file__))
template_dir = "templates"
template_file = "admin.htm.template"
create_site_file = "create_site.sh"
remove_site_file = "remove_site.sh"
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
    
    @staticmethod
    def CreateSite(fullname, username, password, url, indexed):
        create_site_path = current_dir + "/" + create_site_file
        create_lock = lockfile.FileLock(create_site_path)
        with create_lock:
            proc = subprocess.Popen([create_site_path, fullname, username, password, url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdoutdata, stderrdata = proc.communicate()
            if proc.returncode == 0:
                return 0
            else:
                return stdoutdata, stderrdata


    @staticmethod
    def RemoveSite(username):
        remove_site_path = current_dir + "/" + remove_site_file
        remove_lock = lockfile.FileLock(remove_site_path)
        with remove_lock:
            proc = subprocess.Popen([remove_site_path, username], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdoutdata, stderrdata = proc.communicate()
            if proc.returncode == 0:
                return 0
            else:
                return stdoutdata, stderrdata
    

class Users:
    def add_user(self, fullname, username, password, url, indexed):
        db.query(("INSERT INTO students (fullname, username, password, url, indexed) "
                    "VALUES (?, ?, ?, ?, ?)"), [fullname, username, password, 'http://' + url + '.code.club', indexed])
    
    def get_students(self):
        self.__sync_db_users()
        return self.__get_db()
    
    def get_indexed_students(self):
        self.__sync_db_users()
        db_users = self.__get_db()
        return [student for student in db_users if student['isindexed']]
    
    def is_available(self, username):
        self.__sync_db_users()
        db_users = self.__get_db()
        system_users = self.__get_system()
        
        system_code_club_usernames = [u['username'] for u in system_users]
        db_usernames = [u['username'] for u in db_users]

        current_usernames = system_code_club_usernames + db_usernames

        if username in current_usernames:
            return False
        else:
            return True

    def remove_user(self, username):
        db.query("DELETE FROM students WHERE username=?", [username])
    
    def is_student(self, username):
        c = db.query("SELECT username FROM students WHERE username=?", [username])
        result = c.fetchone()
        if result:
            return True
        else:
            return False
        
    def __sync_db_users(self):
        db_users = self.__get_db()
        system_users = self.__get_system()
        
        system_code_club_usernames = [u['username'] for u in system_users if u['gecos'] == "Code Club student"]
        db_usernames = [u['username'] for u in db_users]
        orphaned_usernames = list(set(system_code_club_usernames) - set(db_usernames))
        if len(orphaned_usernames) > 0:
            for username in orphaned_usernames:
                db.query("INSERT INTO students (username) VALUES (?)", [username])
    
    def __get_db(self):
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
        return students
    
    def __get_system(self):
        pwd_users = pwd.getpwall()
        users = []
        for u in pwd_users:
            users.append({
                'username': u[0],
                'password': None,
                'gecos': u[4],
            })
        return users
        
class AdminHandler(tornado.web.RequestHandler):
    def get(self):
        users = Users()
        students = users.get_students()
        template_loader = tornado.template.Loader(current_dir + "/" + template_dir)
        
        output_html = template_loader.load(template_file).generate(students=students)
        self.write(output_html)
        return
    
    def post(self):
        users = Users()
        fullname = escape.xhtml_escape(self.get_argument('fullname'))
        username = escape.xhtml_escape(self.get_argument('username'))
        password = self.get_argument('password')
        url = escape.xhtml_escape(self.get_argument('url'))
        try:
            indexed = 1 if self.get_argument('indexed') == "on" else 0
        except tornado.web.MissingArgumentError:
            indexed = 0
        
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
            url = username
        
        if not users.is_available(username):
            self.write("This username already exists (%s). Specify the username if two people in your class have the same full name." % username)
            return
        
        create_site = Utils.CreateSite(fullname, username, password, url, indexed)
        if create_site != 0:
            self.write("<pre>%s %s %s %s %r\n" % (fullname, username, password, url, indexed))
            self.write("stdout: %s\nstderr: %s" % (create_site[0], create_site[1]))
            return
        
        users.add_user(fullname, username, password, url, indexed)
        self.redirect("/admin.htm")

class DelHandler(tornado.web.RequestHandler):
    def get(self, username):
        users = Users()
        
        if not users.is_student(username):
            self.write("This username has already been deleted (%s)." % username)
            return

        delete_site = Utils.RemoveSite(username)
        if delete_site != 0:
            self.write("<pre>%s\n" % (username))
            self.write("stdout: %s\nstderr: %s" % (delete_site[0], delete_site[1]))
            return
        users.remove_user(username)
        self.redirect("/admin.htm")


class IndexHandler(tornado.web.RequestHandler):
    def get(self, path):
        if path:
            self.redirect("/")
            return
        users = Users()
        students = users.get_indexed_students()
        
        template_loader = tornado.template.Loader(current_dir + "/" + template_dir)
        output_html = template_loader.load("index.htm.template").generate(students=students)
        self.write(output_html)
        return
        
application = tornado.web.Application([
    (r"/admin.htm", AdminHandler),
    (r"/del/([a-z]+)", DelHandler),
    (r"/(.*)", IndexHandler),
], debug=True)

class DatabaseHandler(object):
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.cur = self.conn.cursor()
    
    def query(self, arg, tuple=()):
        self.cur.execute(arg, tuple)
        self.conn.commit()
        return self.cur
    
    def __del__(self):
        self.conn.close()

if __name__ == "__main__":
    application.listen(8080)
    db = DatabaseHandler(current_dir + "/" + db_file)
    db.query(("CREATE TABLE IF NOT EXISTS students "
            "(fullname TEXT, username TEXT UNIQUE, password TEXT, url TEXT, indexed INT)"))

    tornado.ioloop.IOLoop.instance().start()