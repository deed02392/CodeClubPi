#!/usr/bin/python
import os
import tornado.web
import tornado.ioloop
import tornado.template
import sqlite3
from pprint import pprint

current_dir = os.path.dirname(os.path.realpath(__file__))
conn = None
c = None
template_dir = "templates"
template_file = "admin.htm.template"

db_file = "codeclub.db3"

class MainHandler(tornado.web.RequestHandler):
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

application = tornado.web.Application([
    (r"/", MainHandler),
])

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