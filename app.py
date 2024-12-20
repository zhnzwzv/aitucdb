from flask import Flask, render_template, request, redirect, session, url_for, send_file, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from openpyxl import Workbook
from io import BytesIO

app = Flask(__name__)
app.secret_key = '3f7a1b9e9b2d3c4a1dbf431c2d8a1b5c'

# Настройки для подключения к базе данных
def get_db_connection():
    conn = psycopg2.connect(
        host="127.0.0.1",
        database="aituc",  # замените на вашу базу данных
        user="postgres",    # замените на ваше имя пользователя
        password="0301"     # замените на ваш пароль
    )
    return conn

# Главная страница с формой
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        full_name = request.form['fullName']
        birth_date = request.form['birthDate']
        city = request.form['city']
        address = request.form['address']
        phone_number = request.form['phoneNumber']
        group = request.form['group']
        mother_name = request.form['motherName']
        mother_work = request.form['motherWork']
        father_name = request.form['fatherName']
        father_work = request.form['fatherWork']
        mother_phone = request.form['motherPhone']
        father_phone = request.form['fatherPhone']
        family_type = request.form['familyType']    
        living_with = request.form['livingWith']
        
        # Дополнительные данные с учетом пустых значений
        previous_address = request.form.get('previousAddress') or None
        social_status = request.form.get('socialStatus') or None
        hobbies = request.form.get('hobbies') or None
        nationality = request.form.get('nationality') or None
        citizenship = request.form.get('citizenship') or None
        rwp_or_vnz = request.form.get('rwpOrVnz') or None
        document_expiration = request.form.get('documentExpiration') or None
        loss_of_breadwinner = request.form.get('lossOfBreadwinner') or None
        is_pensioner = request.form.get('isPensioner') == 'on'
        is_disabled = request.form.get('isDisabled') == 'on'
        is_orphan = request.form.get('isOrphan') == 'on'
        is_guardian = request.form.get('isGuardian') == 'on'


        # Подключение к базе данных
        conn = get_db_connection()
        cur = conn.cursor()

        # Вставка данных в таблицу
        cur.execute('''
            INSERT INTO students (full_name, birth_date, city, address, phone_number, group_name, 
                                  mother_name, mother_work, father_name, father_work, 
                                  mother_phone, father_phone, family_type, living_with,
                                  previous_address, social_status, hobbies, nationality, citizenship,
                                  rwp_or_vnz, document_expiration, loss_of_breadwinner, is_pensioner,
                                  is_disabled, is_orphan, is_guardian)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (full_name, birth_date, city, address, phone_number, group, 
              mother_name, mother_work, father_name, father_work, 
              mother_phone, father_phone, family_type, living_with,
              previous_address, social_status, hobbies, nationality, citizenship,
              rwp_or_vnz, document_expiration, loss_of_breadwinner, is_pensioner,
              is_disabled, is_orphan, is_guardian))

        # Сохранение изменений и закрытие соединения
        conn.commit()
        cur.close()
        conn.close()

        return redirect('/')


# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Проверка на пустые поля
        if not username or not password:
            return "Логин и пароль не могут быть пустыми", 400  # Возвращаем ошибку

        # Проверка логина и пароля
        if username == 'aitucadmins2024' and password == '1234432156788765':
            session['logged_in'] = True  # Сохраняем информацию о входе
            return redirect('/admin')  # Перенаправление на страницу админа
        else:
            return "Неверный логин или пароль", 403  # Страница ошибки для неверного ввода

    return render_template('login.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Начальный SQL-запрос
    query = """
    SELECT id, full_name, birth_date, city, address, phone_number, group_name, 
           mother_name, mother_work, father_name, father_work, 
           mother_phone, father_phone, family_type, living_with, 
           previous_address, social_status, hobbies, nationality, citizenship, 
           rwp_or_vnz, document_expiration, loss_of_breadwinner, 
           CASE WHEN is_pensioner THEN 'Да' ELSE 'Нет' END AS is_pensioner,
           CASE WHEN is_disabled THEN 'Да' ELSE 'Нет' END AS is_disabled,
           CASE WHEN is_orphan THEN 'Да' ELSE 'Нет' END AS is_orphan,
           CASE WHEN is_guardian THEN 'Да' ELSE 'Нет' END AS is_guardian
    FROM students
    """

    # Условия фильтрации
    conditions = []
    params = []

    if request.method == 'POST':
        # Фильтр по возрасту
        age = request.form.get('age')
        if age:
            conditions.append("EXTRACT(YEAR FROM age(birth_date)) = %s")
            params.append(age)

        # Фильтры по текстовым полям
        filters = {
            "full_name": "name",
            "city": "city",
            "phone_number": "phone",
            "group_name": "group",
            "family_type": "family_type",
            "living_with": "living_with",
            "social_status": "social_status",
            "nationality": "nationality",
            "citizenship": "citizenship",
            "rwp_or_vnz": "rwp_or_vnz",
        }

        for column, field in filters.items():
            value = request.form.get(field)
            if value:
                conditions.append(f"{column} ILIKE %s")
                params.append(f"%{value}%")

        # Фильтры по булевым значениям
        boolean_filters = {
            "is_pensioner": "is_pensioner",
            "is_disabled": "is_disabled",
            "is_orphan": "is_orphan",
            "is_guardian": "is_guardian",
            "loss_of_breadwinner": "loss_of_breadwinner",
        }

        for column, field in boolean_filters.items():
            value = request.form.get(field)
            if value == 'on':  # Флажок включен
                conditions.append(f"{column} = TRUE")

        # Фильтр по дате срока действия документа
        document_expiration = request.form.get('document_expiration')
        if document_expiration:
            conditions.append("document_expiration = %s")
            params.append(document_expiration)

    # Добавляем условия в запрос
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    cur.execute(query, params)
    students = cur.fetchall()

    # Закрываем соединение
    cur.close()
    conn.close()

    # Передаем данные в шаблон
    return render_template('admin.html', students=students)


# Экспорт в Excel
@app.route('/export', methods=['GET'])
def export_to_excel():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Получаем данные из базы данных
    cur.execute("""
        SELECT full_name, birth_date, city, address, phone_number, group_name, 
           mother_name, mother_work, father_name, father_work, 
           mother_phone, father_phone, family_type, living_with,
           previous_address, social_status, hobbies, nationality, citizenship,
           rwp_or_vnz, document_expiration, loss_of_breadwinner, 
           is_pensioner, is_disabled, is_orphan, is_guardian
        FROM students
            """)
    students = cur.fetchall()

    cur.close()
    conn.close()

    # Создаем Excel-файл
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Students Data"

    # Заголовки столбцов
    headers = [
    "Full Name", "Birth Date", "City", "Address", "Phone Number", "Group Name",
    "Mother Name", "Mother Work", "Father Name", "Father Work",
    "Mother Phone", "Father Phone", "Family Type", "Living With",
    "Previous Address", "Social Status", "Hobbies", "Nationality", "Citizenship",
    "RWP or VNZ", "Document Expiration", "Loss of Breadwinner",
    "Is Pensioner", "Is Disabled", "Is Orphan", "Is Guardian"
    ]
    sheet.append(headers)

    # Добавляем данные студентов
    for student in students:
        sheet.append([
        student['full_name'], student['birth_date'], student['city'], student['address'],
        student['phone_number'], student['group_name'], student['mother_name'], 
        student['mother_work'], student['father_name'], student['father_work'], 
        student['mother_phone'], student['father_phone'], student['family_type'], 
        student['living_with'], student['previous_address'], student['social_status'],
        student['hobbies'], student['nationality'], student['citizenship'],
        student['rwp_or_vnz'], student['document_expiration'], student['loss_of_breadwinner'],
        student['is_pensioner'], student['is_disabled'], student['is_orphan'],
        student['is_guardian']
        ])


    # Сохраняем файл в памяти
    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    # Отправляем файл пользователю
    return send_file(output, as_attachment=True, download_name="students_data.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Обработка выхода
@app.route('/logout')
def logout():
    session.pop('logged_in', None)  # Удаляем информацию о сессии
    return redirect('/')

@app.route('/edit_student_page/<int:id>', methods=['GET'])
def edit_student_page(id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM students WHERE id = %s', (id,))
    student = cur.fetchone()
    cur.close()
    conn.close()

    if student:
        return render_template('edit_page_student.html', student=student)
    return "Студент не найден", 404


# Обработчик для редактирования студента
@app.route('/edit_student/<int:id>', methods=['POST'])
def edit_student(id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Получаем новые данные из формы
    full_name = request.form['full_name']
    birth_date = request.form['birth_date']
    city = request.form['city']
    address = request.form['address']
    phone_number = request.form['phone_number']
    group_name = request.form['group_name']
    mother_name = request.form['mother_name']
    mother_work = request.form['mother_work']
    father_name = request.form['father_name']
    father_work = request.form['father_work']
    mother_phone = request.form['mother_phone']
    father_phone = request.form['father_phone']
    family_type = request.form['family_type']
    living_with = request.form['living_with']

    # Обновляем данные в базе данных
    cur.execute("""
        UPDATE students SET full_name = %s, birth_date = %s, city = %s, address = %s, phone_number = %s, 
            group_name = %s, mother_name = %s, mother_work = %s, father_name = %s, father_work = %s, 
            mother_phone = %s, father_phone = %s, family_type = %s, living_with = %s WHERE id = %s
    """, (full_name, birth_date, city, address, phone_number, group_name, mother_name, mother_work, father_name, father_work,
          mother_phone, father_phone, family_type, living_with, id))
    conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for('admin'))

@app.route('/delete_student/<int:id>', methods=['POST'])
def delete_student(id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM students WHERE id = %s", (id,))
    conn.commit()

    cur.close()
    conn.close()

    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True)
