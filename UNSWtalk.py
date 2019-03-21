#!/web/cs2041/bin/python3.6.3
	
# written by andrewt@cse.unsw.edu.au October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/

import os, re, glob, datetime, subprocess
from flask import Flask, render_template, session, request, \
url_for, redirect

students_dir = "static/dataset-medium";

app = Flask(__name__)

# Show unformatted details for student "n"
# Increment n and store it in the session cookie

@app.route('/', methods=['GET','POST'])
@app.route('/start', methods=['GET','POST'])
@app.route('/login', methods=['POST', 'GET'])
def login():
    zid = request.form.get('zid', '')
    zid = re.sub("[^z\d]", "", zid)
    password = request.form.get('password', '')

    student_data = student_info()
    try:
        pw = student_data[zid]['password']  
    except: 
        return render_template('test.html')

    if pw != password:
        return render_template('test.html')
    else:
        session['zid'] = zid
        return redirect(url_for('profile', username=zid), code=307)

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('zid', None)
    return redirect(url_for('login'))

@app.route('/search', methods=['POST', 'GET'])
def search():
    if 'zid' not in session:
        return redirect(url_for('login'))

    student_data = student_info()
    substring = request.form.get('search_name', '')
    
    search_results = []
    for zid in student_data:
        if substring.lower() in student_data[zid]['full_name'].lower():
            search_results.append((student_data[zid]['full_name'], zid, \
                                  os.path.join("dataset-medium", zid, "img.jpg")))
 
    return render_template('search.html', results=search_results)

@app.route('/search_post', methods=['POST', 'GET'])
def search_post():
    all_posts = {}
    substring = request.form.get('post_search', '')
    student_data = student_info()
    for student in student_data.keys():
        temp = post_info(student, [])
        list_to_remove = [] 
        for post_num in temp.keys():
            if substring in temp[post_num]['message']:
                continue
            found = 0
            for comm_num in temp[post_num].keys():
                if not re.search("[0-9]", comm_num):
                    continue
                if substring in temp[post_num][comm_num]['message']:
                    found = 1
                    break
                for reply_num in temp[post_num][comm_num].keys():
                    if not re.search("[0-9]", reply_num):
                        continue
                    if substring in temp[post_num][comm_num][reply_num]['message']:
                        found = 1
                        break
            if found == 0:
                list_to_remove.append(post_num)

        for i in list_to_remove:
            temp.pop(i, None)
        all_posts[student] = temp
            
    return render_template('post_search.html', a=all_posts)

def create_post(username, file_name, msg):
    post_time = str(datetime.datetime.now())
    post_time = re.sub(" ", "T", post_time)
    post_time = re.sub("\.[0-9]+", "+0000", post_time)
    post_time = 'time: ' + post_time + '\n'       
    from_usr = 'from: ' + session.get('zid') + '\n' 
    msg = re.sub(": ", "", msg)
    msg = 'message: ' + msg + '\n'
    new_msg = msg + post_time + from_usr

    f = open(file_name, 'wt')
    f.write(new_msg)
    f.close()

@app.route('/<username>/create_comment/<post_num>', methods=['POST', 'GET'])
def create_comment(username=None, post_num=None):
    count = 0
    while os.path.isfile(os.path.join(students_dir, username, str(post_num) + "-" + str(count) + ".txt")):
        count += 1
    f_file = os.path.join(students_dir, username, str(post_num) + "-" + str(count) + ".txt")
    create_post(username, f_file, request.form.get('comment_post'))

    return redirect(url_for('profile', username=username))    

@app.route('/<username>/create_reply/<post_num>/<comm_num>', methods=['POST', 'GET'])
def create_reply(username=None, post_num=None, comm_num=None):
    count = 0
    while os.path.isfile(os.path.join(students_dir, username, str(post_num) \
                         + "-" + str(comm_num) + "-" + str(count) + ".txt")):
        count += 1
    f_file = os.path.join(students_dir, username, str(post_num) + "-" + str(comm_num) \
                          + "-" + str(count) + ".txt")
    create_post(username, f_file, request.form.get('reply_post'))

    return redirect(url_for('profile', username=username))

@app.route('/<username>/edit_profile', methods=['POST', 'GET'])
def edit_profile(username=None):
    student_data = student_info()
    return render_template('edit_profile.html', student_details=student_data, username=username)

@app.route('/<username>/update_profile', methods=['POST', 'GET'])
def update_profile(username=None):
    new_info = ''
    for dets in ['birthday', 'courses', 'email', 'home_suburb', 'home_longitude', \
                 'full_name', 'home_latitude', 'zid', 'friends', 'password', 'program', 'interests']:
        if request.form.get(dets, '') != '':
            new_info = request.form.get(dets, '')
            break
            
    if new_info == '':
        return redirect(url_for('edit_profile', username=username))

    file_name = os.path.join(students_dir, username, "student.txt")
    new_contents = ''
    with open(file_name) as f:
        for line in f:
            if re.search(dets + ": ", line):
                line = re.sub(dets + ": .*", dets + ": " + new_info, line)
            new_contents += line

    if request.form.get('interests', '') != '':
        new_contents = re.sub("interests: .*\n", "", new_contents) 
        new_contents = new_contents + "interests: " + request.form.get('interests', '') + "\n"

    file_name = os.path.join(students_dir, username, "student.txt")
    f = open(file_name, 'wt')
    f.write(new_contents)
    f.close()

    return redirect(url_for('edit_profile', username=username))

@app.route('/<username>/edit_friends', methods=['POST', 'GET'])
def edit_friends(username=None):
    student_data = student_info()
    friends = student_data[username]['friends']
    friends = friends.split(', ')

    friend_details = []
    for i in friends:
        if i == '':
            continue
        name = student_data[i]['full_name']
        friend_details.append((name, os.path.join("dataset-medium", i, "img.jpg"), i))
    return render_template('edit_friends.html', friends_list=friend_details)    

@app.route('/<username>/delete_friend', methods=['POST', 'GET'])
def delete_friend(username=None):
    file_name = os.path.join(students_dir, session.get('zid'), "student.txt")
    new_file = ""
    with open(file_name) as f:
        for line in f:
            if re.search("friends: ", line):
                line = re.sub(username + ", ", "", line)
                line = re.sub(", " + username, "", line)
                line = re.sub(username, "", line)
            new_file += line
    f = open(file_name, 'wt')
    f.write(new_file)
    f.close()

    return redirect(url_for('edit_friends', username=session.get('zid')))

@app.route('/send_password', methods=['POST', 'GET'])
def send_password():
    zid = request.form.get('zid', '')
    first_name = request.form.get('first_name', '').lower()
    last_name = request.form.get('last_name', '').lower()
    email = request.form.get('email_retrieve', '')
    full_name = first_name + " " + last_name
    student_data = student_info();

    for dets in [zid, first_name, last_name, email]:
        if dets == '':
            return redirect(url_for('login'))
    
    file_name = os.path.join(students_dir, zid, "student.txt")
    if not os.path.isfile(file_name):
        return redirect(url_for('login'))
    
    with open(file_name) as f:
        details = f.read()
        if re.search("full_name: " + full_name, details.lower()) and \
                      re.search("zid: " + zid, details) and \
                      re.search("email: " + email, details):
            # testing purposes - i will send to myself to show assessors
            generate_email("allanlai1998@hotmail.com", "UNSWtalk Password Retrieval", "Password: " \
                           + student_data[zid]['password'])
    return redirect(url_for('login'))

@app.route('/send_email', methods=['POST', 'GET'])
def send_email():
    # re.sub anything that isn't a number, letter or @ 
    full_name = request.form.get('first_name', '') + " " + request.form.get('last_name', '')
    zid = request.form.get('student_zid', '')
    email = request.form.get('email', '')
    signup_pw = request.form.get('signup_pw', '')
    confirm_pw = request.form.get('signup_pw_confirm', '')
    student_data = student_info()

    for i in [full_name, zid, email, signup_pw, confirm_pw]:
        if i == '' or signup_pw != confirm_pw:
            return redirect(url_for('login'))

    new_student = "full_name: " + full_name + "\n" + "zid: " + zid + "\n" \
                   + "email: " + email + "\n" + "password: " + signup_pw + "\n" \
                   + "friends: ()\n" + "program: unknown\n" + "birthday: unknown\n"

    if zid in os.listdir(students_dir):
        return redirect(url_for('login'))
    else:
        os.mkdir(os.path.join(students_dir, zid))

    file_name = os.path.join(students_dir, zid, "student_draft.txt")
    f = open(file_name, 'wt')
    f.write(new_student)
    f.close()

    generate_email(email, "UNSWtalk Activation Link", url_for('validate_account', _external=True, username=zid))
    
    return redirect(url_for('login'))

# credits to cse - code from email
def generate_email(to, subject, message):
    mutt = [
            'mutt',
            '-s',
            subject,
            '-e', 'set copy=no',
            '-e', 'set realname=UNSWtalk',
            '--', to
    ]

    subprocess.run(
            mutt,
            input = message.encode('utf8'),
            stderr = subprocess.PIPE,
            stdout = subprocess.PIPE,
    )

@app.route('/<username>/validate_account', methods=['POST', 'GET'])
def validate_account(username=None):
    return render_template('create_account.html', username=username)

@app.route('/<username>/activate_acc', methods=['POST', 'GET'])
def activate_acc(username=None):
    old_file = os.path.join(students_dir, username, "student_draft.txt")    
    new_file = os.path.join(students_dir, username, "student.txt")
    os.rename(old_file, new_file)

    return redirect(url_for('login'))

@app.route('/<username>/profile', methods=['POST', 'GET'])
def profile(username=None):
    if request.form.get('msg_post'):
        count = 0
        while os.path.isfile(os.path.join(students_dir, username, str(count) + ".txt")):
            count += 1 
        f_file = os.path.join(students_dir, username, str(count) + ".txt")
        create_post(username, f_file, request.form.get('msg_post'))
        
    if 'zid' not in session:
        return redirect(url_for('login'))

    img_path = os.path.join("dataset-medium", username, "img.jpg")
    student_data = student_info() 

    friends = student_data[username]['friends']
    friends = friends.split(', ')
    posts = post_info(username, friends)
    
    friend_details = []
    for i in friends:
        if i == '':
            continue
        name = student_data[i]['full_name']
        friend_details.append((name, os.path.join("dataset-medium", i, "img.jpg"), i))
               
    details_show = ['full_name', 'zid', 'birthday', 'program']
    details = ""
    for i in details_show:
        details = details + i + ': ' + student_data[username][i] + '\n'

    return render_template('start.html', student_details=student_data, jpg=img_path, \
               all_posts=posts, friends_list=friend_details, username=username)

@app.route('/<username>/make_post', methods=['POST', 'GET'])
def make_post(username=None):
    return render_template('post.html', username=username)

@app.route('/<username>/make_comment/<post_num>', methods=['POST', 'GET'])
def make_comment(username=None, post_num=None):
    post_data = post_info(username, [])
    return render_template('comment.html', username=username, post_num=post_num, post_data=post_data)

@app.route('/<username>/make_reply/<post_num>/<comm_num>', methods=['POST', 'GET'])
def make_reply(username=None, post_num=None, comm_num=None):
    post_data = post_info(username, [])
    return render_template('reply.html', username=username, post_num=post_num, comm_num=comm_num, post_data=post_data)

def student_info():
    all_data = {}
    for student in os.listdir(students_dir):
        if not os.path.isfile(os.path.join(students_dir, student, "student.txt")):
            continue

        details_filename = os.path.join(students_dir, student, "student.txt")
        with open(details_filename) as f:
            details = f.read()
            details = re.sub("[\(\)]", "", details)
            # credit due here - https://stackoverflow.com/questions/4627981/creating-a-dictionary-from-a-string
            all_data[student] = dict((k, v) for k, v in (item.split(': ') for \
                                     item in details.split('\n') if item != ''))
    return all_data

def post_info(username, friends):
    all_data = {}
    post_list = []
    comment_list = []
    reply_list = []

    file_path = os.path.join(students_dir, username)
    for file in sorted(os.listdir(file_path), reverse=True):
       if "student.txt" in file:
           continue
       if "img.jpg" in file:
           continue
       
       with open(os.path.join(students_dir, username, file)) as f:
           if "message: " not in f.read():
               continue 

       if re.search("^[0-9]+\.txt", file): post_list.append(file)
       if re.search("^[0-9]+-[0-9]+\.txt", file): comment_list.append(file)
       if re.search("^[0-9]+-[0-9]+-[0-9]+\.txt", file): reply_list.append(file)

    for post in post_list:
        post_num = re.search("([0-9]+)", post)
        post_num = post_num.group(1)
        post_to_open = os.path.join(students_dir, username, post)
        with open(post_to_open) as f:
            all_data.setdefault(post_num, {})
            for line in f:
                list = line.split(': ')
                all_data[post_num].update({list[0]:list[1]})
        
        for comment in comment_list:
            comm_num = re.search("([0-9]+)-([0-9]+)", comment)
            parent_num = comm_num.group(1)
            comm_num = comm_num.group(2)
            if parent_num != post_num:
                continue   

            comment_to_open = os.path.join(students_dir, username, comment)
            with open(comment_to_open) as f:
                all_data[post_num].setdefault(comm_num, {})
                for line in f:
                    list = line.split(': ')
                    all_data[post_num][comm_num].update({list[0]:list[1]})

            for reply in reply_list:
                temp = re.search("([0-9]+)-([0-9]+)-([0-9]+)", reply)
                reply_num = temp.group(3)
                if temp.group(1) != post_num or temp.group(2) != comm_num:
                    continue
                
                reply_to_open = os.path.join(students_dir, username, reply)
                with open(reply_to_open) as f:
                    all_data[post_num][comm_num].setdefault(reply_num, {})
                    for line in f:
                        list = line.split(': ')
                        all_data[post_num][comm_num][reply_num].update({list[0]:list[1]}) 
       
    return all_data
        
if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True, port=4999)
