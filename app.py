from flask import Flask, render_template, g, request, session, redirect, url_for
from database import get_db,connect_db
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g,'sqlite_db'):
        g.sqlite_db.close()


def get_current_user():
    user_result = None
    if 'user' in session:
        user = session['user']

        db = get_db()
        cur = db.execute("select id,name,password,expert,admin from users where name = ?",[user])
        user_result = cur.fetchone()

    return user_result
        
@app.route('/')
def index():
    user = get_current_user()
    db = get_db()
    cur = db.execute('select questions.id as question_id,questions.question_text,askers.name as asker_name,experts.name as expert_name from questions \
        join users as askers on askers.id = questions.asked_by \
            join users as experts on experts.id = questions.expert_id where questions.answer_text is not null')
    
    questions = cur.fetchall()
    return render_template('home.html',user = user,questions = questions)


@app.route('/register',methods = ['GET','POST'])
def register():
    user = get_current_user()
    if request.method == 'POST':

        name = request.form['name']
        password = request.form['password']
        db = get_db()
        hashed_pass = generate_password_hash(password,method='sha256')
        db.execute("insert into users (name, password, expert, admin) values (?,?,?,?)",[name,hashed_pass,'0','0'])
        db.commit()
        
        session['user'] = request.form['name']

        return redirect(url_for('index'))

    return render_template('register.html',user = user)


@app.route('/login',methods = ['GET','POST'])
def login():
    user = get_current_user()
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        db = get_db()
        cur = db.execute("select name,password from users where name = ?",[name])
        user_result = cur.fetchone()
        if check_password_hash(user_result['password'],password):
            session['user'] = user_result['name']
            return redirect(url_for('index'))
        else:
            return "False"
    return render_template('login.html',user = user)


@app.route('/question/<id>')
def question(id):
    user = get_current_user()
    db = get_db()
    cur = db.execute('select questions.question_text,questions.answer_text,askers.name as asker_name,experts.name as expert_name from questions \
        join users as askers on askers.id = questions.asked_by \
            join users as experts on experts.id = questions.expert_id where questions.id = ?',[id])
    
    result = cur.fetchone()
    return render_template('question.html',user = user,answer = result)


@app.route('/answer/<ques_id>',methods = ['GET','POST'])
def answer(ques_id):
    user = get_current_user()

    db = get_db()
    if request.method == 'POST':
        db.execute('update questions set answer_text = ? where id = ?',[request.form['answer'],ques_id])
        db.commit()
        return redirect(url_for('unanswered'))
    question_cur = db.execute('select id,question_text from questions where id = ?',[ques_id])
    ques_text = question_cur.fetchone()
    return render_template('answer.html',user = user, question = ques_text)


@app.route('/ask',methods = ['POST','GET'])
def ask():
    user = get_current_user()
    db = get_db()
    if request.method == 'POST':
        question = request.form['question']
        expert_id = request.form['expert']
        db.execute("insert into questions (question_text,asked_by,expert_id) values (?,?,?)",[question,user['id'],expert_id])
        db.commit() 
        return redirect(url_for('index'))

    cur = db.execute("select id,name from users where expert = ?",[1])
    experts = cur.fetchall()
    
    return render_template('ask.html',user = user,experts = experts)


@app.route('/unanswered')
def unanswered():
    user = get_current_user()
    db = get_db()
    ques_cur = db.execute('select questions.id, questions.question_text, users.name from questions \
        join users on users.id = questions.asked_by where questions.answer_text is null and questions.expert_id = ?',[user['id']])
    ques = ques_cur.fetchall()
    return render_template('unanswered.html',user = user, questions = ques)


@app.route('/users')
def users():
    user = get_current_user()

    db = get_db()
    users_cur = db.execute('select id, name, expert, admin from users')
    user_results = users_cur.fetchall()
    return render_template('users.html',user = user,users = user_results)


@app.route('/promote/<user_id>')
def promote(user_id):
    db = get_db()
    db.execute('update users set expert = 1 where id = ?',[user_id])
    db.commit()
    return redirect(url_for('users'))

@app.route('/logout')
def logout():
    session.pop('user',None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug  = True)