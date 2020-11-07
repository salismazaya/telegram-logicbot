import sqlite3, os

DATABASE_PATH = "database.db"

class Connection:
	def __init__(self, db, cur):
		self.db = db
		self.cur = cur

def needDb(func, *message):
	def inner(*args, **kwargs):
		db = sqlite3.connect(DATABASE_PATH)
		cur = db.cursor()

		rv = func(Connection(db, cur), *message, *args, **kwargs)

		cur.close()
		db.close()
		return rv
	return inner