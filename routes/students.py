from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Student

students_bp = Blueprint('students', __name__)

@students_bp.route('/students')
def list_students():
    students = Student.query.all()
    return render_template('students.html', students=students)

@students_bp.route('/students/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        roll_no = request.form['roll_no']
        course = request.form['course']
        email = request.form['email']

        new_student = Student(name=name, roll_no=roll_no, course=course, email=email)
        db.session.add(new_student)
        db.session.commit()
        flash('Student added successfully!', 'success')
        return redirect(url_for('students.list_students'))

    return render_template('add_student.html')

@students_bp.route('/students/delete/<int:id>', methods=['POST'])
def delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted successfully!', 'info')
    return redirect(url_for('students.list_students'))
