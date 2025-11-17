from flask import Blueprint, render_template
from models import db, Student, Course

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
def reports_home():
    students = Student.query.all()
    courses = Course.query.all()
    return render_template('reports.html', students=students, courses=courses)
