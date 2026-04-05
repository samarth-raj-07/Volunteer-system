from flask import Flask, request, jsonify, session
from flask_cors import CORS
import mysql.connector
import hashlib
import os
from datetime import date

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "volunteer_secret_key_2025")
CORS(app, supports_credentials=True)


# ─── DB CONNECTION (SAFE VERSION) ────────────────────────────
import os
import mysql.connector
from urllib.parse import urlparse

def get_db_connection():
    try:
        db_url = os.getenv("MYSQL_PUBLIC_URL")   # 👈 THIS LINE IS KEY

        url = urlparse(db_url)

        return mysql.connector.connect(
            host=url.hostname,
            user=url.username,
            password=url.password,
            database=url.path.replace("/", ""),
            port=url.port
        )
    except Exception as e:
        print("DB ERROR:", e)
        return None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ─── ROOT ROUTE ───────────────────────────────────────────────
@app.route('/')
def home():
    return "Volunteer System API is running 🚀"


# ─── AUTH ROUTES ──────────────────────────────────────────────

@app.route('/api/register/volunteer', methods=['POST'])
def register_volunteer():
    data = request.json
    db = get_db()

    if not db:
        return jsonify({'success': False, 'message': 'DB connection failed'}), 500

    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            "INSERT INTO Volunteer (name, email, phone, city, password) VALUES (%s,%s,%s,%s,%s)",
            (data['name'], data['email'], data.get('phone'), data.get('city'), hash_password(data['password']))
        )
        db.commit()

        vid = cursor.lastrowid

        cursor.execute(
            "INSERT INTO VolunteerProfile (volunteer_id, experience_level, availability_hours, preferred_mode) VALUES (%s,%s,%s,%s)",
            (vid, data.get('experience_level','Beginner'), data.get('availability_hours',5), data.get('preferred_mode','Online'))
        )
        db.commit()

        return jsonify({'success': True, 'volunteer_id': vid}), 201

    except mysql.connector.IntegrityError:
        return jsonify({'success': False, 'message': 'Email already exists'}), 409

    finally:
        cursor.close()
        db.close()


@app.route('/api/register/organization', methods=['POST'])
def register_organization():
    data = request.json
    db = get_db()

    if not db:
        return jsonify({'success': False, 'message': 'DB connection failed'}), 500

    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            "INSERT INTO Organization (org_name, email, phone, address, description, password) VALUES (%s,%s,%s,%s,%s,%s)",
            (data['org_name'], data['email'], data.get('phone'), data.get('address'), data.get('description'), hash_password(data['password']))
        )
        db.commit()

        return jsonify({'success': True, 'org_id': cursor.lastrowid}), 201

    except mysql.connector.IntegrityError:
        return jsonify({'success': False, 'message': 'Email already exists'}), 409

    finally:
        cursor.close()
        db.close()


@app.route('/api/login/volunteer', methods=['POST'])
def login_volunteer():
    data = request.json
    db = get_db()

    if not db:
        return jsonify({'success': False, 'message': 'DB connection failed'}), 500

    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT volunteer_id, name, email, city FROM Volunteer WHERE email=%s AND password=%s",
        (data['email'], hash_password(data['password']))
    )

    user = cursor.fetchone()

    cursor.close()
    db.close()

    if user:
        session['user'] = user
        session['role'] = 'volunteer'
        return jsonify({'success': True, 'user': user, 'role': 'volunteer'})

    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401


@app.route('/api/login/organization', methods=['POST'])
def login_organization():
    data = request.json
    db = get_db()

    if not db:
        return jsonify({'success': False, 'message': 'DB connection failed'}), 500

    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT org_id, org_name, email FROM Organization WHERE email=%s AND password=%s",
        (data['email'], hash_password(data['password']))
    )

    org = cursor.fetchone()

    cursor.close()
    db.close()

    if org:
        session['user'] = org
        session['role'] = 'organization'
        return jsonify({'success': True, 'user': org, 'role': 'organization'})

    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})


# ─── OPPORTUNITIES ───────────────────────────────────────────

@app.route('/api/opportunities', methods=['GET'])
def get_opportunities():
    db = get_db()

    if not db:
        return jsonify({'success': False, 'message': 'DB connection failed'}), 500

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT o.opp_id, o.title, o.location, o.mode, o.start_date, o.end_date,
               o.hours_required, o.category, o.description,
               og.org_name
        FROM Opportunity o
        JOIN Organization og ON o.org_id = og.org_id
        ORDER BY o.start_date
    """)

    data = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify(data)


# ─── RUN APP ────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# from flask import Flask, request, jsonify, session
# from flask_cors import CORS
# import mysql.connector
# import hashlib
# import os
# from datetime import date

# app = Flask(__name__)
# app.secret_key = 'volunteer_secret_key_2025'
# CORS(app, supports_credentials=True)

# # ─── DB Connection ────────────────────────────────────────────
# # ─── DB Connection (FIXED) ────────────────────────────────────
# def get_db():
#     try:
#         db = mysql.connector.connect(
#             host="localhost",
#             user="root",
#             password="mysql",  # 🔴 PUT YOUR PASSWORD HERE
#             database="volunteer_db"
#         )
#         return db
#     except mysql.connector.Error as err:
#         print("❌ Database connection error:", err)
#         return None

# def hash_password(password):
#     return hashlib.sha256(password.encode()).hexdigest()

# # ─── AUTH ROUTES ──────────────────────────────────────────────

# @app.route('/api/register/volunteer', methods=['POST'])
# def register_volunteer():
#     data = request.json
#     db = get_db()
#     cursor = db.cursor(dictionary=True)
#     try:
#         cursor.execute(
#             "INSERT INTO Volunteer (name, email, phone, city, password) VALUES (%s,%s,%s,%s,%s)",
#             (data['name'], data['email'], data.get('phone'), data.get('city'), hash_password(data['password']))
#         )
#         db.commit()
#         vid = cursor.lastrowid
#         cursor.execute(
#             "INSERT INTO VolunteerProfile (volunteer_id, experience_level, availability_hours, preferred_mode) VALUES (%s,%s,%s,%s)",
#             (vid, data.get('experience_level','Beginner'), data.get('availability_hours',5), data.get('preferred_mode','Online'))
#         )
#         db.commit()
#         return jsonify({'success': True, 'volunteer_id': vid}), 201
#     except mysql.connector.IntegrityError:
#         return jsonify({'success': False, 'message': 'Email already exists'}), 409
#     finally:
#         cursor.close(); db.close()

# @app.route('/api/register/organization', methods=['POST'])
# def register_organization():
#     data = request.json
#     db = get_db()
#     cursor = db.cursor(dictionary=True)
#     try:
#         cursor.execute(
#             "INSERT INTO Organization (org_name, email, phone, address, description, password) VALUES (%s,%s,%s,%s,%s,%s)",
#             (data['org_name'], data['email'], data.get('phone'), data.get('address'), data.get('description'), hash_password(data['password']))
#         )
#         db.commit()
#         return jsonify({'success': True, 'org_id': cursor.lastrowid}), 201
#     except mysql.connector.IntegrityError:
#         return jsonify({'success': False, 'message': 'Email already exists'}), 409
#     finally:
#         cursor.close(); db.close()

# @app.route('/api/login/volunteer', methods=['POST'])
# def login_volunteer():
#     data = request.json
#     db = get_db()
#     cursor = db.cursor(dictionary=True)
#     cursor.execute("SELECT volunteer_id, name, email, city FROM Volunteer WHERE email=%s AND password=%s",
#                    (data['email'], hash_password(data['password'])))
#     user = cursor.fetchone()
#     cursor.close(); db.close()
#     if user:
#         session['user'] = user; session['role'] = 'volunteer'
#         return jsonify({'success': True, 'user': user, 'role': 'volunteer'})
#     return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

# @app.route('/api/login/organization', methods=['POST'])
# def login_organization():
#     data = request.json
#     db = get_db()
#     cursor = db.cursor(dictionary=True)
#     cursor.execute("SELECT org_id, org_name, email FROM Organization WHERE email=%s AND password=%s",
#                    (data['email'], hash_password(data['password'])))
#     org = cursor.fetchone()
#     cursor.close(); db.close()
#     if org:
#         session['user'] = org; session['role'] = 'organization'
#         return jsonify({'success': True, 'user': org, 'role': 'organization'})
#     return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

# @app.route('/api/logout', methods=['POST'])
# def logout():
#     session.clear()
#     return jsonify({'success': True})

# # ─── VOLUNTEER ROUTES ─────────────────────────────────────────

# @app.route('/api/volunteer/<int:vid>/profile', methods=['GET'])
# def get_volunteer_profile(vid):
#     db = get_db(); cursor = db.cursor(dictionary=True)
#     cursor.execute("""
#         SELECT v.name, v.email, v.phone, v.city,
#                vp.experience_level, vp.availability_hours, vp.preferred_mode,
#                GROUP_CONCAT(DISTINCT s.skill_name) AS skills,
#                GROUP_CONCAT(DISTINCT i.interest_name) AS interests
#         FROM Volunteer v
#         LEFT JOIN VolunteerProfile vp ON v.volunteer_id = vp.volunteer_id
#         LEFT JOIN VolunteerSkill vs ON v.volunteer_id = vs.volunteer_id
#         LEFT JOIN Skill s ON vs.skill_id = s.skill_id
#         LEFT JOIN VolunteerInterest vi ON v.volunteer_id = vi.volunteer_id
#         LEFT JOIN Interest i ON vi.interest_id = i.interest_id
#         WHERE v.volunteer_id = %s GROUP BY v.volunteer_id
#     """, (vid,))
#     profile = cursor.fetchone()
#     cursor.close(); db.close()
#     return jsonify(profile)

# @app.route('/api/volunteer/<int:vid>/profile', methods=['PUT'])
# def update_volunteer_profile(vid):
#     data = request.json
#     db = get_db(); cursor = db.cursor()
#     cursor.execute("""UPDATE VolunteerProfile
#         SET experience_level=%s, availability_hours=%s, preferred_mode=%s
#         WHERE volunteer_id=%s""",
#         (data['experience_level'], data['availability_hours'], data['preferred_mode'], vid))
#     db.commit(); cursor.close(); db.close()
#     return jsonify({'success': True})

# @app.route('/api/volunteer/<int:vid>/skills', methods=['POST'])
# def add_volunteer_skill(vid):
#     data = request.json
#     db = get_db(); cursor = db.cursor()
#     cursor.execute("SELECT skill_id FROM Skill WHERE skill_name=%s", (data['skill_name'],))
#     skill = cursor.fetchone()
#     if not skill:
#         cursor.execute("INSERT INTO Skill (skill_name) VALUES (%s)", (data['skill_name'],))
#         db.commit(); skill_id = cursor.lastrowid
#     else:
#         skill_id = skill[0]
#     try:
#         cursor.execute("INSERT INTO VolunteerSkill (volunteer_id, skill_id) VALUES (%s,%s)", (vid, skill_id))
#         db.commit()
#     except: pass
#     cursor.close(); db.close()
#     return jsonify({'success': True})

# @app.route('/api/volunteer/<int:vid>/interests', methods=['POST'])
# def add_volunteer_interest(vid):
#     data = request.json
#     db = get_db(); cursor = db.cursor()
#     cursor.execute("SELECT interest_id FROM Interest WHERE interest_name=%s", (data['interest_name'],))
#     interest = cursor.fetchone()
#     if not interest:
#         cursor.execute("INSERT INTO Interest (interest_name) VALUES (%s)", (data['interest_name'],))
#         db.commit(); interest_id = cursor.lastrowid
#     else:
#         interest_id = interest[0]
#     try:
#         cursor.execute("INSERT INTO VolunteerInterest (volunteer_id, interest_id) VALUES (%s,%s)", (vid, interest_id))
#         db.commit()
#     except: pass
#     cursor.close(); db.close()
#     return jsonify({'success': True})

# # ─── OPPORTUNITY ROUTES ───────────────────────────────────────

# @app.route('/api/opportunities', methods=['GET'])
# def get_opportunities():
#     db = get_db(); cursor = db.cursor(dictionary=True)
#     filters = []
#     params = []
#     location = request.args.get('location')
#     mode = request.args.get('mode')
#     cause = request.args.get('cause')
#     skill = request.args.get('skill')
#     keyword = request.args.get('keyword')

#     query = """SELECT o.opp_id, o.title, o.location, o.mode, o.start_date, o.end_date,
#                       o.hours_required, o.category, o.description,
#                       og.org_name, c.cause_name,
#                       orq.required_skill, orq.minimum_level, orq.volunteers_needed
#                FROM Opportunity o
#                JOIN Organization og ON o.org_id = og.org_id
#                LEFT JOIN Cause c ON o.cause_id = c.cause_id
#                LEFT JOIN OpportunityRequirement orq ON o.opp_id = orq.opp_id"""

#     if location: filters.append("o.location = %s"); params.append(location)
#     if mode: filters.append("o.mode = %s"); params.append(mode)
#     if cause: filters.append("c.cause_name = %s"); params.append(cause)
#     if skill: filters.append("orq.required_skill = %s"); params.append(skill)
#     if keyword: filters.append("(o.title LIKE %s OR o.description LIKE %s)"); params += [f'%{keyword}%', f'%{keyword}%']

#     if filters:
#         query += " WHERE " + " AND ".join(filters)
#     query += " ORDER BY o.start_date"

#     cursor.execute(query, params)
#     opps = cursor.fetchall()
#     cursor.close(); db.close()
#     return jsonify(opps)

# @app.route('/api/opportunities/<int:opp_id>', methods=['GET'])
# def get_opportunity_detail(opp_id):
#     db = get_db(); cursor = db.cursor(dictionary=True)
#     cursor.execute("""SELECT o.*, og.org_name, og.email AS org_email, og.phone AS org_phone,
#                              c.cause_name, orq.required_skill, orq.minimum_level, orq.volunteers_needed,
#                              ROUND(AVG(f.rating),2) AS avg_rating, COUNT(f.feedback_id) AS total_reviews
#                       FROM Opportunity o
#                       JOIN Organization og ON o.org_id = og.org_id
#                       LEFT JOIN Cause c ON o.cause_id = c.cause_id
#                       LEFT JOIN OpportunityRequirement orq ON o.opp_id = orq.opp_id
#                       LEFT JOIN Feedback f ON o.opp_id = f.opp_id
#                       WHERE o.opp_id = %s GROUP BY o.opp_id""", (opp_id,))
#     opp = cursor.fetchone()
#     cursor.close(); db.close()
#     return jsonify(opp)

# @app.route('/api/opportunities', methods=['POST'])
# def post_opportunity():
#     data = request.json
#     db = get_db(); cursor = db.cursor()
#     cursor.execute("""INSERT INTO Opportunity (org_id, cause_id, title, description, location,
#                       category, mode, start_date, end_date, hours_required)
#                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
#         (data['org_id'], data.get('cause_id'), data['title'], data.get('description'),
#          data.get('location'), data.get('category'), data.get('mode'),
#          data.get('start_date'), data.get('end_date'), data.get('hours_required')))
#     db.commit(); opp_id = cursor.lastrowid
#     if data.get('required_skill'):
#         cursor.execute("INSERT INTO OpportunityRequirement (opp_id, required_skill, minimum_level, volunteers_needed) VALUES (%s,%s,%s,%s)",
#             (opp_id, data['required_skill'], data.get('minimum_level','Beginner'), data.get('volunteers_needed',10)))
#         db.commit()
#     cursor.close(); db.close()
#     return jsonify({'success': True, 'opp_id': opp_id}), 201

# # ─── APPLICATION ROUTES ───────────────────────────────────────

# @app.route('/api/apply', methods=['POST'])
# def apply_opportunity():
#     data = request.json
#     db = get_db(); cursor = db.cursor(dictionary=True)
#     cursor.execute("SELECT COUNT(*) AS cnt FROM Application WHERE volunteer_id=%s AND opp_id=%s",
#                    (data['volunteer_id'], data['opp_id']))
#     if cursor.fetchone()['cnt'] > 0:
#         cursor.close(); db.close()
#         return jsonify({'success': False, 'message': 'Already applied'}), 409
#     cursor.execute("INSERT INTO Application (volunteer_id, opp_id, applied_date) VALUES (%s,%s,%s)",
#                    (data['volunteer_id'], data['opp_id'], date.today()))
#     db.commit(); cursor.close(); db.close()
#     return jsonify({'success': True}), 201

# @app.route('/api/application/<int:app_id>/status', methods=['PUT'])
# def update_application_status(app_id):
#     data = request.json
#     db = get_db(); cursor = db.cursor()
#     cursor.execute("UPDATE Application SET status=%s WHERE application_id=%s",
#                    (data['status'], app_id))
#     if data['status'] == 'Accepted':
#         cursor.execute("SELECT volunteer_id, opp_id FROM Application WHERE application_id=%s", (app_id,))
#         row = cursor.fetchone()
#         if row:
#             cursor.execute("INSERT IGNORE INTO Participation (volunteer_id, opp_id, participation_date) VALUES (%s,%s,%s)",
#                            (row[0], row[1], date.today()))
#     db.commit(); cursor.close(); db.close()
#     return jsonify({'success': True})

# @app.route('/api/volunteer/<int:vid>/applications', methods=['GET'])
# def get_volunteer_applications(vid):
#     db = get_db(); cursor = db.cursor(dictionary=True)
#     cursor.execute("""SELECT a.application_id, o.title, og.org_name, a.applied_date, a.status,
#                              o.location, o.mode, o.start_date
#                       FROM Application a
#                       JOIN Opportunity o ON a.opp_id = o.opp_id
#                       JOIN Organization og ON o.org_id = og.org_id
#                       WHERE a.volunteer_id = %s ORDER BY a.applied_date DESC""", (vid,))
#     apps = cursor.fetchall()
#     cursor.close(); db.close()
#     return jsonify(apps)

# @app.route('/api/organization/<int:org_id>/applications', methods=['GET'])
# def get_org_applications(org_id):
#     db = get_db(); cursor = db.cursor(dictionary=True)
#     cursor.execute("""SELECT a.application_id, v.name AS volunteer_name, v.email, v.phone,
#                              o.title, a.applied_date, a.status, a.opp_id
#                       FROM Application a
#                       JOIN Volunteer v ON a.volunteer_id = v.volunteer_id
#                       JOIN Opportunity o ON a.opp_id = o.opp_id
#                       WHERE o.org_id = %s ORDER BY a.applied_date DESC""", (org_id,))
#     apps = cursor.fetchall()
#     cursor.close(); db.close()
#     return jsonify(apps)

# # ─── FEEDBACK ROUTES ──────────────────────────────────────────

# @app.route('/api/feedback', methods=['POST'])
# def submit_feedback():
#     data = request.json
#     db = get_db(); cursor = db.cursor()
#     cursor.execute("INSERT INTO Feedback (volunteer_id, opp_id, rating, comment, feedback_date) VALUES (%s,%s,%s,%s,%s)",
#                    (data['volunteer_id'], data['opp_id'], data['rating'], data.get('comment'), date.today()))
#     db.commit(); cursor.close(); db.close()
#     return jsonify({'success': True}), 201

# @app.route('/api/opportunity/<int:opp_id>/feedback', methods=['GET'])
# def get_opportunity_feedback(opp_id):
#     db = get_db(); cursor = db.cursor(dictionary=True)
#     cursor.execute("""SELECT v.name, f.rating, f.comment, f.feedback_date
#                       FROM Feedback f JOIN Volunteer v ON f.volunteer_id = v.volunteer_id
#                       WHERE f.opp_id = %s ORDER BY f.feedback_date DESC""", (opp_id,))
#     feedbacks = cursor.fetchall()
#     cursor.close(); db.close()
#     return jsonify(feedbacks)

# # ─── RECOMMENDATION ROUTE ─────────────────────────────────────

# @app.route('/api/volunteer/<int:vid>/recommendations', methods=['GET'])
# def get_recommendations(vid):
#     db = get_db(); cursor = db.cursor(dictionary=True)
#     cursor.execute("""SELECT DISTINCT o.opp_id, o.title, o.location, o.mode,
#                              o.start_date, o.hours_required, og.org_name, c.cause_name,
#                              'skill' AS match_type
#                       FROM Opportunity o
#                       JOIN Organization og ON o.org_id = og.org_id
#                       LEFT JOIN Cause c ON o.cause_id = c.cause_id
#                       JOIN OpportunityRequirement orq ON o.opp_id = orq.opp_id
#                       JOIN Skill sk ON orq.required_skill = sk.skill_name
#                       JOIN VolunteerSkill vs ON sk.skill_id = vs.skill_id
#                       WHERE vs.volunteer_id = %s
#                         AND o.opp_id NOT IN (SELECT opp_id FROM Application WHERE volunteer_id = %s)
#                       UNION
#                       SELECT DISTINCT o.opp_id, o.title, o.location, o.mode,
#                              o.start_date, o.hours_required, og.org_name, c.cause_name,
#                              'interest' AS match_type
#                       FROM Opportunity o
#                       JOIN Organization og ON o.org_id = og.org_id
#                       LEFT JOIN Cause c ON o.cause_id = c.cause_id
#                       JOIN VolunteerInterest vi ON vi.volunteer_id = %s
#                       JOIN Interest i ON vi.interest_id = i.interest_id
#                       WHERE LOWER(c.cause_name) LIKE CONCAT('%%', LOWER(i.interest_name), '%%')
#                         AND o.opp_id NOT IN (SELECT opp_id FROM Application WHERE volunteer_id = %s)
#                       ORDER BY start_date LIMIT 10""",
#                    (vid, vid, vid, vid))
#     recs = cursor.fetchall()
#     cursor.close(); db.close()
#     return jsonify(recs)

# # ─── PARTICIPATION & STATS ROUTES ────────────────────────────

# @app.route('/api/volunteer/<int:vid>/participation', methods=['GET'])
# def get_participation(vid):
#     db = get_db(); cursor = db.cursor(dictionary=True)
#     cursor.execute("""SELECT p.participation_id, o.title, og.org_name,
#                              p.participation_date, p.hours_worked
#                       FROM Participation p
#                       JOIN Opportunity o ON p.opp_id = o.opp_id
#                       JOIN Organization og ON o.org_id = og.org_id
#                       WHERE p.volunteer_id = %s ORDER BY p.participation_date DESC""", (vid,))
#     history = cursor.fetchall()
#     cursor.close(); db.close()
#     return jsonify(history)

# @app.route('/api/volunteer/<int:vid>/stats', methods=['GET'])
# def get_volunteer_stats(vid):
#     db = get_db(); cursor = db.cursor(dictionary=True)
#     cursor.execute("SELECT COALESCE(SUM(hours_worked),0) AS total_hours, COUNT(*) AS total_participations FROM Participation WHERE volunteer_id=%s", (vid,))
#     stats = cursor.fetchone()
#     cursor.execute("SELECT COUNT(*) AS total_applications FROM Application WHERE volunteer_id=%s", (vid,))
#     stats.update(cursor.fetchone())
#     cursor.close(); db.close()
#     return jsonify(stats)

# @app.route('/api/organization/<int:org_id>/stats', methods=['GET'])
# def get_org_stats(org_id):
#     db = get_db(); cursor = db.cursor(dictionary=True)
#     cursor.execute("""SELECT COUNT(DISTINCT o.opp_id) AS total_opportunities,
#                              COUNT(DISTINCT p.volunteer_id) AS total_volunteers,
#                              COALESCE(SUM(p.hours_worked),0) AS total_hours,
#                              ROUND(AVG(f.rating),2) AS avg_rating
#                       FROM Organization og
#                       LEFT JOIN Opportunity o ON og.org_id = o.org_id
#                       LEFT JOIN Participation p ON o.opp_id = p.opp_id
#                       LEFT JOIN Feedback f ON o.opp_id = f.opp_id
#                       WHERE og.org_id = %s""", (org_id,))
#     stats = cursor.fetchone()
#     cursor.close(); db.close()
#     return jsonify(stats)

# @app.route('/api/causes', methods=['GET'])
# def get_causes():
#     db = get_db(); cursor = db.cursor(dictionary=True)
#     cursor.execute("SELECT * FROM Cause")
#     causes = cursor.fetchall()
#     cursor.close(); db.close()
#     return jsonify(causes)

# @app.route('/api/skills', methods=['GET'])
# def get_skills():
#     db = get_db(); cursor = db.cursor(dictionary=True)
#     cursor.execute("SELECT * FROM Skill")
#     skills = cursor.fetchall()
#     cursor.close(); db.close()
#     return jsonify(skills)

# if __name__ == '__main__':
#     app.run(debug=True, port=5000)
