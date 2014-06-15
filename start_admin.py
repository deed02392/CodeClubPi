#!/usr/bin/python
import os
import sys
import signal
import re
import pwd
import binascii
import tornado.web
import tornado.ioloop
import tornado.template
import json
import sqlite3
import random
import subprocess
import lockfile
from tornado import escape
from pprint import pprint
from passlib.context import CryptContext

current_dir = os.path.dirname(os.path.realpath(__file__))
templates_dir = "templates"
static_dir = "static"
create_site_file = "scripts/create_site.sh"
update_site_file = "scripts/update_site.sh"
remove_site_file = "scripts/remove_site.sh"
db_file = "lib/codeclub.db3"
pwd_context = CryptContext(schemes=["sha256_crypt"],default="sha256_crypt")
valid_fullname = re.compile(r"^[A-Za-z]+(?: ?[A-Za-z]+)*$")
valid_username = re.compile(r"^[a-z]+$")

def on_exit(sig, func=None):
    tornado.ioloop.IOLoop.instance().add_callback(shutdown)
    print "Exiting..."
    sys.exit(1)

def shutdown():
    application.stop()
    io_loop = tornado.ioloop.IOLoop.instance()
    deadline = time.time() + 3

    def stop_loop():
        now = time.time()
        if now < deadline and (io_loop._callbacks or io_loop._timeouts):
            io_loop.add_timeout(now + 1, stop_loop)
        else:
            io_loop.stop()
    stop_loop()
    del db

def jtable_reply(ok, data=None):
    return_dict = {}
    if ok:
        return_dict['Result'] = "OK"
        if type(data) is list:
            return_dict['Records'] = data
        elif type(data) is dict:
            return_dict['Record'] = data
    else:
        return_dict['Result'] = "ERROR"
        if data:
            return_dict['Message'] = data
    return json.dumps(return_dict)

def string_cap(s, l):
    return s if len(s)<=l else s[0:l-3]+'...'

def fullname_to_username(fullname):
    fullname = fullname.lower()
    fullname = ''.join(fullname.split()) # Kill whitespace
    fullname = string_cap(fullname, 30)
    if valid_username.match(fullname):
        return fullname
    else:
        return False

def create_password():
    zoo_animals = ['elephant', 'lion', 'tiger', 'giraffe', 'penguin', 'gorillas', 'sharks',
        'panda', 'meerkat', 'crocodile', 'bear', 'otter', 'wolf', 'cheetah', 'snake', 'zebra',
        'frog', 'dolphin']
    fruits = ['strawberry', 'mango', 'watermelon', 'banana', 'orange', 'apple', 'grape',
        'peach', 'cherry', 'raspberry', 'kiwi', 'blueberry', 'lemon', 'pear', 'plum',
        'blackberry', 'lime']
    rand = random.SystemRandom()
    number = rand.randint(1, 1000)
    return rand.choice(fruits) + rand.choice(zoo_animals) + str(number)

def create_site(fullname, username, password, url, indexed):
    create_site_path = os.path.join(current_dir, create_site_file)
    create_lock = lockfile.FileLock(create_site_path)
    with create_lock:
        proc = subprocess.Popen([create_site_path, fullname, username, password, url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdoutdata, stderrdata = proc.communicate()
        if proc.returncode == 0:
            return 0
        else:
            return stdoutdata, stderrdata

def update_site(username, password):
    update_site_path = os.path.join(current_dir, update_site_file)
    update_lock = lockfile.FileLock(update_site_path)
    with update_lock:
        proc = subprocess.Popen([update_site_path, username, password], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdoutdata, stderrdata = proc.communicate()
        if proc.returncode == 0:
            return 0
        else:
            return stdoutdata, stderrdata
            
def remove_site(username):
    remove_site_path = os.path.join(current_dir, remove_site_file)
    remove_lock = lockfile.FileLock(remove_site_path)
    with remove_lock:
        proc = subprocess.Popen([remove_site_path, username], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdoutdata, stderrdata = proc.communicate()
        if proc.returncode == 0:
            return 0
        else:
            return stdoutdata, stderrdata

def hash_password(password, salt=None):
    if not salt:
        salt = binascii.hexlify(os.urandom(32))
    
    return scrypt.encrypt(salt, password, hash_for_secs), salt

class Users:
    def add_user(self, fullname, username, password, url, indexed):
        db.query(("INSERT INTO students (fullname, username, password, url, indexed) "
                    "VALUES (?, ?, ?, ?, ?)"), [fullname, username, password, url, indexed])
    
    def get_students(self, sortby, sortway):
        self.__sync_db_users()
        return self.__get_db(sortby, sortway)
    
    def get_indexed_students(self):
        self.__sync_db_users()
        db_users = self.get_students('fullname', 'ASC')
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
    
    def update_user(self, fullname, username, password, indexed):
        db.query("UPDATE students SET fullname=?, password=?, indexed=? WHERE username=?", [fullname, password, indexed, username])
    
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
    
    def __get_db(self, sortby=None, sortway=None):
        order_by = None
        if sortby and sortby.lower() in ['fullname']:
            if sortway and sortway.upper() in ['ASC', 'DESC']:
                order_by = " ORDER BY %s %s" % (sortby.lower(), sortway.upper())
        
        query = "SELECT fullname, username, password, url, indexed FROM students" + (order_by if order_by else "")
        c = db.query(query)
        students = []
        for record in c.fetchall():
            students.append({
                'fullname': record[0] if record[0] else "<em>Unknown</em>",
                'username': record[1],
                'password': record[2] if record[2] else "<em>Encrypted</em>",
                'url': record[3] if record[3] else "",
                'isindexed': record[4] if record[4] else 0,
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

class AuthenticatedRequestHandler(tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        super(AuthenticatedRequestHandler, self).__init__(*args, **kwargs)
    def get_current_user(self):
        return self.get_secure_cookie("logged_in")

class AdminHandler(AuthenticatedRequestHandler):
    
    @tornado.web.authenticated
    def get(self):
        self.render("admin.htm.template")

class LogoutHandler(AuthenticatedRequestHandler):
    
    @tornado.web.authenticated
    def get(self):
        self.clear_all_cookies()
        self.redirect("/")

class FirstPasswordHandler(tornado.web.RequestHandler):
    def post(self):
        c = db.query("SELECT password FROM admin WHERE oid=1")
        unset_password = True if c.fetchone() is None else False
        new_password = self.get_argument('new-password', '')
        confirm_new_password = self.get_argument('confirm-new-password', '')

        if unset_password and new_password:
            if new_password == confirm_new_password:
                password = pwd_context.encrypt(new_password)
                db.query(("INSERT OR REPLACE INTO admin (oid, password) "
                            "VALUES (1, ?)"), [password])
                self.write("OK");
            else:
                self.write("Passwords did not match. Please re-enter.")
        else:
            self.write("You must set a password, else anyone can delete all work!")
            
class PasswordHandler(AuthenticatedRequestHandler):
    
    @tornado.web.authenticated
    def post(self):
        current_password = self.get_argument('current-password', '')
        new_password = self.get_argument('new-password', '')
        confirm_new_password = self.get_argument('confirm-new-password', '')
        
        c = db.query("SELECT password FROM admin WHERE oid=1")
        hashed_password = c.fetchone()[0]
        if not pwd_context.verify(current_password, hashed_password):
            self.write("Current password is incorrect.")
            return
        
        if new_password:
            if new_password == confirm_new_password:
                password = pwd_context.encrypt(new_password)
                db.query(("INSERT OR REPLACE INTO admin (oid, password) "
                            "VALUES (1, ?)"), [password])
                self.write("OK");
            else:
                self.write("Passwords did not match. Please re-enter.")
        else:
            self.write("You must set a password, else anyone can delete all work!")

class AjaxAddHandler(AuthenticatedRequestHandler):
    
    @tornado.web.authenticated
    def post(self):
        users = Users()
        fullname = escape.xhtml_escape(self.get_argument('fullname', ''))
        username = escape.xhtml_escape(self.get_argument('username', ''))
        password = self.get_argument('password', '')
        url = escape.xhtml_escape(self.get_argument('url', ''))
        indexed = 1 if self.get_argument('isindexed', '') else 0
        
        if not fullname:
            self.write(jtable_reply(False, "Full Name must be specified"))
            return
        elif not valid_fullname.match(fullname):
            self.write(jtable_reply(False, "Full Name must just be letters with a single space separating the names"))
            return
        
        if not username:
            username = fullname_to_username(fullname)
            if not username:
                self.write(jtable_reply(False, "Please specify a username, I couldn't create one from %s" % fullname))
                return
        if not password:
            password = create_password()
        if not url:
            url = username
        
        if not users.is_available(username):
            self.write(jtable_reply(False, "This username already exists (%s). Specify the username if two people in your class have the same full name." % username))
            return
        
        add_site = create_site(fullname, username, password, url, indexed)
        if add_site != 0:
            self.write(jtable_reply(False, "%s %s %s %s %r\n" % (fullname, username, password, url, indexed)))
            self.write(jtable_reply(False, "stdout: %s\nstderr: %s" % (add_site[0], add_site[1])))
            return
        
        url = 'http://' + url + '.code.club';
        users.add_user(fullname, username, password, url, indexed)
        self.write(jtable_reply(True, {
            'fullname': fullname,
            'username': username,
            'password': password,
            'url': url,
            'isindexed': indexed,
        }))

class AjaxListHandler(AuthenticatedRequestHandler):
    
    @tornado.web.authenticated
    def post(self):
        users = Users()
        sorting = escape.xhtml_escape(self.get_argument('jtSorting', ''))
        sortby = None
        sortway = None
        if sorting:
            sortby, sortway = sorting.split()
        
        records = users.get_students(sortby, sortway)
        if records:
            self.write(jtable_reply(True, records))
        else:
            self.write(jtable_reply(False))

class AjaxDeleteHandler(AuthenticatedRequestHandler):
    
    @tornado.web.authenticated
    def post(self):
        users = Users()
        username = escape.xhtml_escape(self.get_argument('username'))
        if not users.is_student(username):
            self.write(jtable_reply(True))
            return
        
        delete_site = remove_site(username)
        if delete_site != 0:
            self.write(jtable_reply(
                False,
                ("System error deleting user (%s)."
                            "stdout: %s"
                            "stderr: %s") % (username, delete_site[0], delete_site[1])
            ))
            return
        users.remove_user(username)
        self.write(jtable_reply(True))

class AjaxUpdateHandler(AuthenticatedRequestHandler):
    
    @tornado.web.authenticated
    def post(self):
        users = Users()
        fullname = escape.xhtml_escape(self.get_argument('fullname'))
        username = escape.xhtml_escape(self.get_argument('username'))
        password = escape.xhtml_escape(self.get_argument('password'))
        indexed = 1 if self.get_argument('isindexed', '') else 0
        
        if not users.is_student(username):
            self.write(jtable_reply(False, "This user does not exist - refresh the page and try again."))
            return
        
        if not fullname:
            self.write(jtable_reply(False, "You must specify the Full Name of this student."))
            return
        elif not valid_fullname.match(fullname):
            self.write(jtable_reply(False, "Full Name must just be letters with a single space separating the names"))
            return
        
        if not password:
            password = create_password()
        
        update_site_ret = update_site(username, password)
        if update_site_ret != 0:
            self.write(jtable_reply(
                False,
                ("System error deleting user (%s)."
                            "stdout: %s"
                            "stderr: %s") % (username, update_site_ret[0], update_site_ret[1])
            ))
            return
        
        users.update_user(fullname, username, password, indexed)
        self.write(jtable_reply(True, {
            'fullname': fullname,
            'password': password,
            'isindexed': indexed
        }))

class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        c = db.query("SELECT password FROM admin WHERE oid=1")
        hashed_password = c.fetchone()
        unset_password = True if hashed_password is None else False
        self.render("login.htm.template", unset_password=unset_password)
        return
    
    def post(self):
        password = self.get_argument('password', '')
        if not password:
            self.write("ERROR")
            return
        
        c = db.query("SELECT password FROM admin WHERE oid=1")
        hashed_password = c.fetchone()[0]
        
        if pwd_context.verify(password, hashed_password):
            self.set_secure_cookie("logged_in", "admin")
            self.write("OK")
        else:
            self.write("ERROR")

class IndexHandler(tornado.web.RequestHandler):
    def get(self, path):
        if path:
            self.redirect("/")
            return
        users = Users()
        students = users.get_indexed_students()
        
        self.render("index.htm.template", students=students)

class PoweroffHandler(AuthenticatedRequestHandler):
    
    @tornado.web.authenticated
    def get(self):
        os.system("poweroff")

application = tornado.web.Application([
    (r"/admin.htm", AdminHandler),
    (r"/logout", LogoutHandler),
    (r"/pass", PasswordHandler),
    (r"/firstpass", FirstPasswordHandler),
    (r"/ajax/students-add", AjaxAddHandler),
    (r"/ajax/students-list", AjaxListHandler),
    (r"/ajax/students-update", AjaxUpdateHandler),
    (r"/ajax/students-delete", AjaxDeleteHandler),
    (r"/poweroff", PoweroffHandler),
    (r"/login.htm", LoginHandler),
    (r"/(.*)", IndexHandler),
],
debug=True,
login_url="/login.htm",
cookie_secret=binascii.hexlify(os.urandom(32)),
template_path=os.path.join(current_dir, templates_dir),
static_path=os.path.join(current_dir, static_dir))

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
    application.listen(8080, "127.0.0.1")
    db = DatabaseHandler(os.path.join(current_dir, db_file))
    db.query(("CREATE TABLE IF NOT EXISTS students "
            "(fullname TEXT, username TEXT UNIQUE, password TEXT, url TEXT, indexed INT)"))
    db.query(("CREATE TABLE IF NOT EXISTS admin "
            "(password TEXT NOT NULL)"))
    
    signal.signal(signal.SIGTERM, on_exit)
    signal.signal(signal.SIGINT, on_exit)
    
    tornado.ioloop.IOLoop.instance().start()