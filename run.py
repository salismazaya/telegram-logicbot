# coded by: salismazaya
# 07 - 11 - 2020

from telebot import TeleBot
from db import needDb
from module import *
import os, random, pandas as pd

YOUR_TELEGRAM_BOT_API = "1461493189:AAGnHrXXXXXXXXXXXX"

bot = TeleBot(YOUR_TELEGRAM_BOT_API)

home_button = button(["Get Question", "Rank", "My Point"])

@bot.message_handler(commands = ["start", "home"])
def start(message):
	bot.send_message(message.from_user.id, f"Hi {message.from_user.first_name}!", reply_markup = home_button)

@bot.message_handler(commands = ["question"])
@bot.message_handler(func = lambda x: x.text == "Get Question")
@needDb
def question(conn, message):
	conn.cur.execute("SELECT current_answerId FROM user WHERE id = {}".format(message.from_user.id))
	output = conn.cur.fetchone()

	if not output:
		question, answer = generateQuestion()

		randNum = str(random.randint(0,10000))
		question.save(randNum + ".jpg")

		questionList = [random.randint(0,180), random.randint(0,180), random.randint(0,180), answer]
		random.shuffle(questionList)
		questionList = inline(questionList[:2], questionList[2:])

		data = bot.send_photo(message.from_user.id, open(randNum + ".jpg", "rb"), reply_markup = questionList)
		os.remove(randNum + ".jpg")

		try:
			conn.cur.execute(f"INSERT INTO user VALUES({message.from_user.id}, '{removeBoldItalic(message.from_user.username)}', 0, {answer}, {data.message_id})")
			conn.db.commit()
		except:
			pass

	else:
		if output[0]:
			try:
				bot.edit_message_reply_markup(message.from_user.id, output[0])
			except:
				pass

		question, answer = generateQuestion()

		randNum = str(random.randint(0,10000))
		question.save(randNum + ".jpg")

		questionList = [random.randint(0,180), random.randint(0,180), random.randint(0,180), answer]
		random.shuffle(questionList)
		questionList = inline(questionList[:2], questionList[2:])

		data = bot.send_photo(message.from_user.id, open(randNum + ".jpg", "rb"), reply_markup = questionList)
		os.remove(randNum + ".jpg")

		conn.cur.execute(f"UPDATE user SET current_answer = {answer}, current_answerId = {data.message_id} WHERE id = {message.from_user.id}")
		conn.db.commit()


@bot.callback_query_handler(func = lambda x: x.data.replace("-", "", 1).isdigit())
@needDb
def answering(conn, call):
	bot.answer_callback_query(callback_query_id = call.id, text = "You choose " + call.data)

	try:
		bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
	except:
		pass

	conn.cur.execute(f"SELECT current_answer, point FROM user WHERE id = {call.message.chat.id}")
	trueAnswer, point = conn.cur.fetchone()


	if int(call.data) == trueAnswer:
		bot.send_message(call.message.chat.id, "You are right point +1")
		conn.cur.execute(f"UPDATE user SET current_answer = NULL, current_answerId = NULL, point = {point + 1} WHERE id = {call.message.chat.id}")

	else:
		bot.send_message(call.message.chat.id, "You are wrong point -1")
		conn.cur.execute(f"UPDATE user SET current_answer = NULL, current_answerId = NULL, point = {point - (1 if point > 0 else 0)} WHERE id = {call.message.chat.id}")

	conn.db.commit()

@bot.message_handler(commands = ["mypoint"])
@bot.message_handler(func = lambda x: x.text == "My Point")
@needDb
def mypoint(conn, message):
	conn.cur.execute(f"SELECT name, point FROM user WHERE id = {message.from_user.id}")
	data = conn.cur.fetchone()

	if not data:
		return

	bot.send_message(message.from_user.id, f"Username: *{data[0]}*\nYour points: *{data[1]}*", parse_mode = "Markdown")

@bot.message_handler(commands = ["rank"])
@bot.message_handler(func = lambda x: x.text == "Rank")
@needDb
def rank(conn, message):
	conn.cur.execute("SELECT name, point FROM user")
	data = conn.cur.fetchall()

	if not data:
		return

	df = pd.DataFrame(data).sort_values(1, ascending = False)
	user = df[0].tolist()
	point = df[1].tolist()

	string = "Highest Point List\n" 

	sorted_data = list(zip(user, point))
	for i, x in enumerate(sorted_data[:10]):
		string += f"\n{i + 1}. {x[0]}, *{x[1]} point*"

	bot.send_message(message.from_user.id, string, parse_mode = "Markdown")


print("Bot started !!")

bot.infinity_polling()