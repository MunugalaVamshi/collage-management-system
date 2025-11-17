from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Course

courses_bp = Blueprint('courses', __name__)

@courses_bp.route('/courses')
def list_courses():
    courses = Course.query.all()
    return render_template('courses.html', courses=courses)

@courses_bp.route('/courses/add', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        course_name = request.form['course_name']
        description = request.form['description']
        credits = request.form['credits']

        new_course = Course(course_name=course_name, description=description, credits=credits)
        db.session.add(new_course)
        db.session.commit()
        flash('Course added successfully!', 'success')
        return redirect(url_for('courses.list_courses'))
    return render_template('add_course.html')

@courses_bp.route('/courses/delete/<int:id>', methods=['POST'])
def delete_course(id):
    course = Course.query.get_or_404(id)
    db.session.delete(course)
    db.session.commit()
    flash('Course deleted successfully!', 'info')
    return redirect(url_for('courses.list_courses'))
