import os
import urllib.parse
import json
import base64
import cv2
import numpy as np
import face_recognition
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_this_later' 

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'attendance.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- WHATSAPP GROUP LINKS ---
SUBJECT_GROUPS = {
    "Operating System": "https://chat.whatsapp.com/GlkuWa1NF5EAmaRiJXknxJ",
    "Software Engineering": "https://chat.whatsapp.com/EiXy94poebVHMEm8mJ2eXS",
    "OOP": "https://chat.whatsapp.com/BDbvoBvSpCF0A9NpdbdOpU",
    "Artificial Intelligence": "https://chat.whatsapp.com/GKla8rGTWuA7qsnhK9lTVh",
    "Compiler Design": "https://chat.whatsapp.com/CJjap6DGwLs6Nf1a05ECA8",
    "Industrial Management": "https://chat.whatsapp.com/L5FAw8gqyUNGfJCxxef2zT?s=sh&p=a&mlu=0&ilr=4",
    "Operating System Lab": "https://chat.whatsapp.com/BDmV2RpP7mg8n5SrVqjxVZ?s=cl&p=a&mlu=4&ilr=4",
    "OOP Lab": "https://chat.whatsapp.com/BDbvoBvSpCF0A9NpdbdOpU",
    "Software Engineering Lab": "https://chat.whatsapp.com/EiXy94poebVHMEm8mJ2eXS"
}

# --- DATABASE MODELS ---
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_roll = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    face_encoding = db.Column(db.Text, nullable=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    subject = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(10), nullable=False)

def decode_base64_image(base64_string):
    if ',' in base64_string:
        base64_string = base64_string.split(',')[1]
    img_data = base64.b64decode(base64_string)
    nparr = np.frombuffer(img_data, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

# --- APP ROUTES ---
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        session['stream'] = request.form.get('stream')
        session['semester'] = request.form.get('semester')
        return redirect(url_for('attendance'))
    return render_template('home.html')

@app.route('/attendance')
def attendance():
    if 'stream' not in session:
        return redirect(url_for('home'))
        
    current_stream = session.get('stream')
    current_semester = session.get('semester')
    
    if current_stream == "CSE" and current_semester == "5th":
        students = Student.query.all()
    else:
        students = [] 
        
    today_date_obj = date.today()
    today_date = today_date_obj.strftime("%B %d, %Y")
    
    submitted_records = Attendance.query.filter_by(date=today_date_obj).all()
    submitted_subjects = list(set([r.subject for r in submitted_records]))
    
    return render_template('index.html', 
                           students=students, 
                           date=today_date,
                           stream=current_stream,
                           semester=current_semester,
                           submitted_subjects=submitted_subjects)

@app.route('/submit', methods=['POST'])
def submit_attendance():
    selected_subject = request.form.get('subject')
    
    if Attendance.query.filter_by(date=date.today(), subject=selected_subject).first():
        return f"Error: Attendance for {selected_subject} has already been submitted today. Please go back."
    
    students = Student.query.all()
    present_students = []
    
    for student in students:
        form_field_name = f'status_{student.id}'
        is_checked = request.form.get(form_field_name)
        
        final_status = "Present" if is_checked else "Absent"
        
        if final_status == "Present":
            present_students.append(student) 
            
        new_record = Attendance(
            student_id=student.id, 
            date=date.today(), 
            subject=selected_subject, 
            status=final_status
        )
        db.session.add(new_record)
            
    if students:
        db.session.commit()
    
    msg_text = f"*Date:* {date.today().strftime('%d-%b-%Y')}\n*Subject:* {selected_subject}\n\n*Present Students:*\n"
    for i, student in enumerate(present_students, 1):
        msg_text += f"{i}) {student.class_roll}--> {student.name}\n"
        
    encoded_msg = urllib.parse.quote(msg_text)
    group_link = SUBJECT_GROUPS.get(selected_subject, "https://chat.whatsapp.com/GKla8rGTWuA7qsnhK9lTVh")
    
    return redirect(url_for('view_attendance', 
                            filter_date=date.today().strftime('%Y-%m-%d'),
                            filter_subject=selected_subject,
                            filter_status='Present',
                            encoded_msg=encoded_msg, 
                            group_link=group_link))

@app.route('/view')
def view_attendance():
    filter_date_str = request.args.get('filter_date')
    filter_subject = request.args.get('filter_subject') 
    filter_status = request.args.get('filter_status', 'Present')
    encoded_msg = request.args.get('encoded_msg') 
    group_link = request.args.get('group_link') 
    
    query = db.session.query(Attendance, Student).join(Student)
    
    if filter_date_str:
        try:
            filter_date_obj = datetime.strptime(filter_date_str, '%Y-%m-%d').date()
            query = query.filter(Attendance.date == filter_date_obj)
        except ValueError:
            pass
            
    if filter_subject:
        query = query.filter(Attendance.subject == filter_subject)
        
    if filter_status:
        query = query.filter(Attendance.status == filter_status)
            
    records = query.order_by(Attendance.date.desc()).all()
    
    return render_template('view.html', 
                           records=records, 
                           filter_date=filter_date_str, 
                           filter_subject=filter_subject,
                           filter_status=filter_status,
                           encoded_msg=encoded_msg, 
                           group_link=group_link)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form.get('name')
        class_roll = request.form.get('class_roll')
        roll_number = request.form.get('roll_number')
        if name and class_roll and roll_number:
            new_student = Student(class_roll=class_roll, name=name, roll_number=roll_number)
            db.session.add(new_student)
            db.session.commit()
            return redirect(url_for('attendance'))
    return render_template('add_student.html')

@app.route('/lab')
def lab_dashboard():
    students = Student.query.order_by(Student.class_roll).all()
    
    # Capture filter requests
    filter_date_str = request.args.get('filter_date')
    filter_subject = request.args.get('filter_subject')
    
    lab_subjects = ["Operating System Lab", "OOP Lab", "Software Engineering Lab"]
    
    # Base query: Only Lab subjects AND strictly Present students
    query = db.session.query(Attendance, Student).join(Student).filter(
        Attendance.subject.in_(lab_subjects),
        Attendance.status == "Present"
    )
    
    # Apply date filter if selected
    if filter_date_str:
        try:
            filter_date_obj = datetime.strptime(filter_date_str, '%Y-%m-%d').date()
            query = query.filter(Attendance.date == filter_date_obj)
        except ValueError:
            pass
            
    # Apply subject filter if selected
    if filter_subject:
        query = query.filter(Attendance.subject == filter_subject)
            
    records = query.order_by(Attendance.date.desc()).all()
    
    return render_template('lab.html', 
                           students=students, 
                           records=records,
                           filter_date=filter_date_str,
                           filter_subject=filter_subject)
@app.route('/register_face', methods=['POST'])
def register_face():
    student_id = request.form.get('student_id')
    image_data = request.form.get('image_data')
    
    img = decode_base64_image(image_data)
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    encodings = face_recognition.face_encodings(rgb_img)
    if not encodings:
        return "No face detected. Please try again."
        
    face_encoding_json = json.dumps(encodings[0].tolist())
    
    student = Student.query.get(student_id)
    student.face_encoding = face_encoding_json
    db.session.commit()
    
    return "Face registered successfully!"

@app.route('/send_lab_report')
def send_lab_report():
    subject = request.args.get('subject')
    date_str = request.args.get('date')
    
    if not subject:
        return {"error": "Please select a specific Lab Session first."}
        
    try:
        filter_date_obj = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
    except ValueError:
        filter_date_obj = date.today()
        
    # Strictly fetch only the selected subject
    records = db.session.query(Attendance, Student).join(Student).filter(
        Attendance.subject == subject,
        Attendance.date == filter_date_obj,
        Attendance.status == "Present"
    ).all()
    
    msg_text = f"*Date:* {filter_date_obj.strftime('%d-%b-%Y')}\n*Subject:* {subject}\n\n*Present Students:*\n"
    
    if not records:
        msg_text += "No students marked present.\n"
    else:
        for i, (att, student) in enumerate(records, 1):
            msg_text += f"{i}) {student.class_roll}--> {student.name}\n"
            
    # Get the specific link for the selected lab group
    group_link = SUBJECT_GROUPS.get(subject, "https://web.whatsapp.com")
    
    return {"message": msg_text, "group_link": group_link}
@app.route('/lab_attendance', methods=['POST'])
def lab_attendance():
    subject = request.form.get('subject')
    image_data = request.form.get('image_data')
    
    img = decode_base64_image(image_data)
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    unknown_encodings = face_recognition.face_encodings(rgb_img)
    if not unknown_encodings:
        return "No face detected. Please ensure you are in a well-lit area."
        
    unknown_encoding = unknown_encodings[0]
    
    students = Student.query.filter(Student.face_encoding.isnot(None)).all()
    if not students:
        return "No students are registered with facial recognition."
        
    known_encodings = [np.array(json.loads(s.face_encoding)) for s in students]
    
    face_distances = face_recognition.face_distance(known_encodings, unknown_encoding)
    best_match_index = np.argmin(face_distances)
    
    if face_distances[best_match_index] < 0.45:
        matched_student = students[best_match_index]
        
        existing_record = Attendance.query.filter_by(
            date=date.today(), 
            subject=subject, 
            student_id=matched_student.id
        ).first()
        
        if existing_record:
            return f"Attendance already marked for {matched_student.name} today."
        
        new_record = Attendance(student_id=matched_student.id, subject=subject, status="Present")
        db.session.add(new_record)
        db.session.commit()
        
        return f"✅ Attendance successfully marked for {matched_student.class_roll} - {matched_student.name}!"
    else:
        return "❌ Face not recognized. Please register your face or try again."

# --- AUTOMATIC INITIALIZATION ---
with app.app_context():
    db.create_all()
    
    if not Student.query.first():
        real_students = [
            Student(class_roll="CSE-20/24", name="ARIJIT SARKAR", roll_number="11800124002"),
            Student(class_roll="CSE-22/24", name="SK ISAM HAQUE", roll_number="11800124004"),
            Student(class_roll="N/A", name="MD. SAMIRUZZAMAN", roll_number="11800124005"),
            Student(class_roll="CSE- 35/24", name="INDRAJIT MONDAL", roll_number="11800124006"),
            Student(class_roll="CSE- 12/24", name="ROHAN KARMAKAR", roll_number="11800124007"),
            Student(class_roll="CSE- 04/24", name="ARKADIP CHAKRABORTY", roll_number="11800124008"),
            Student(class_roll="CSE- 21/24", name="MOUSUMI DEY", roll_number="11800124010"),
            Student(class_roll="CSE- 23/24", name="MD NAFIS", roll_number="11800124011"),
            Student(class_roll="CSE- 24/24", name="BAPPA KABIRAJ", roll_number="11800124012"),
            Student(class_roll="CSE- 25/24", name="JOY KUMAR BHALLA", roll_number="11800124013"),
            Student(class_roll="CSE- 29/24", name="KRISHNENDU DAS", roll_number="11800124014"),
            Student(class_roll="CSE- 33/24", name="SUPRATIM GHOSH", roll_number="11800124016"),
            Student(class_roll="CSE- 05/24", name="RIYODEB DHIBAR", roll_number="11800124019"),
            Student(class_roll="CSE- 03/24", name="SHWETARKA BANERJEE", roll_number="11800124021"),
            Student(class_roll="CSE-10/24", name="UMER NAWAZ", roll_number="11800124022"),
            Student(class_roll="CSE- 11/24", name="SAMBIT BHAKAT", roll_number="11800124023"),
            Student(class_roll="N/A", name="ARBIND SINGH", roll_number="11800124024"),
            Student(class_roll="CSE- 15/24", name="SK TARIK AZIZ", roll_number="11800124025"),
            Student(class_roll="CSE- 28/24", name="DEBANJAN DAS", roll_number="11800124026"),
            Student(class_roll="CSE-31/24", name="ISHITA GANAI", roll_number="11800124027"),
            Student(class_roll="CSE- 32/24", name="NISHAR ALI", roll_number="11800124028"),
            Student(class_roll="CSE-D 7/25", name="BISWADEEP BASAK", roll_number="11800125029"),
            Student(class_roll="CSE-D 16/25", name="SAKILUR HAQUE", roll_number="11800125032"),
            Student(class_roll="CSE-D 10/25", name="AYUSH CHAKRABORTY", roll_number="11800125033"),
            Student(class_roll="CSE-D 11/25", name="GOLAP HOSSAIN", roll_number="11800125034"),
            Student(class_roll="CSE-D 12/25", name="ANUP RAJAK", roll_number="11800125035"),
            Student(class_roll="CSE-D 14/25", name="SANJAN SAHA", roll_number="11800125036"),
            Student(class_roll="CSE- D 15/25", name="ALOKE DAS", roll_number="11800125037"),
            Student(class_roll="CSE-D 01/25", name="ADNAN HOSSAIN", roll_number="11800125038"),
            Student(class_roll="CSE- D 02/25", name="DEBOLINA GHOSH", roll_number="11800125039"),
            Student(class_roll="CSE-D 03/25", name="BIKASH CHOWDHURY", roll_number="11800125040"),
            Student(class_roll="CSE-D 05/25", name="FIROJ ANSARI", roll_number="11800125042"),
            Student(class_roll="CSE-D 08/25", name="SAYAN KOLEY", roll_number="11800125043"),
            Student(class_roll="CSE-D 09/25", name="AKASH ADHIKARY", roll_number="11800125044")
        ]
        db.session.bulk_save_objects(real_students)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)