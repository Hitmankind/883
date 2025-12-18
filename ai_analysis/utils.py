"""
AI Analysis Utility Functions
Helper functions for data collection and analysis preparation
"""

from datetime import datetime, timedelta
from django.db.models import Avg, StdDev, Count, Q, Max, Min
from decimal import Decimal
import json

from students.models import Student, Score, Course, Enrollment


def collect_student_data(student):
    """
    Collect comprehensive data for a student

    Args:
        student: Student object

    Returns:
        Dictionary containing student data
    """
    # Get all scores for the student
    scores = Score.objects.filter(student=student).select_related('course')

    # Get enrollments
    enrollments = Enrollment.objects.filter(student=student).select_related('course')

    # Calculate statistics
    total_scores = scores.count()
    if total_scores > 0:
        avg_score = scores.aggregate(avg=Avg('score'))['avg']
        max_score = scores.aggregate(max=Max('score'))['max']
        min_score = scores.aggregate(min=Min('score'))['min']
    else:
        avg_score = max_score = min_score = 0

    # Get course-specific data
    course_data = []
    for course in Course.objects.filter(score__student=student).distinct():
        course_scores = scores.filter(course=course)
        if course_scores.exists():
            course_avg = course_scores.aggregate(avg=Avg('score'))['avg']
            course_count = course_scores.count()

            course_data.append({
                'course_id': course.course_id,
                'course_name': course.course_name,
                'credits': course.credits,
                'average_score': float(course_avg) if course_avg else 0,
                'score_count': course_count,
                'latest_score': float(course_scores.latest('date').score) if course_scores.exists() else 0
            })

    # Calculate GPA (assuming 4.0 scale)
    gpa = calculate_gpa(scores)

    # Recent performance (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_scores = scores.filter(date__gte=thirty_days_ago)
    recent_avg = recent_scores.aggregate(avg=Avg('score'))['avg'] if recent_scores.exists() else 0

    return {
        'student_info': {
            'student_id': student.student_id,
            'name': student.name,
            'college': student.college,
            'major': student.major,
            'gender': student.gender
        },
        'statistics': {
            'total_scores': total_scores,
            'average_score': float(avg_score) if avg_score else 0,
            'gpa': gpa,
            'max_score': float(max_score) if max_score else 0,
            'min_score': float(min_score) if min_score else 0,
            'recent_average': float(recent_avg) if recent_avg else 0,
            'courses_count': len(course_data)
        },
        'scores': [
            {
                'course_id': score.course.course_id,
                'course_name': score.course.course_name,
                'score': float(score.score),
                'date': score.date.isoformat(),
            }
            for score in scores
        ],
        'courses': course_data,
        'enrollments': [
            {
                'course_id': enrollment.course.course_id,
                'course_name': enrollment.course.course_name,
                'enrollment_date': enrollment.enrollment_date.isoformat() if enrollment.enrollment_date else None
            }
            for enrollment in enrollments
        ],
        'data_collection_time': datetime.now().isoformat()
    }


def calculate_gpa(scores):
    """
    Calculate GPA from scores (4.0 scale)

    Args:
        scores: Score queryset

    Returns:
        GPA as float
    """
    if not scores.exists():
        return 0.0

    total_points = 0
    total_credits = 0

    for score in scores:
        # Convert score to grade points
        if score.score >= 90:
            grade_points = 4.0
        elif score.score >= 85:
            grade_points = 3.7
        elif score.score >= 82:
            grade_points = 3.3
        elif score.score >= 78:
            grade_points = 3.0
        elif score.score >= 75:
            grade_points = 2.7
        elif score.score >= 72:
            grade_points = 2.3
        elif score.score >= 68:
            grade_points = 2.0
        elif score.score >= 64:
            grade_points = 1.5
        elif score.score >= 60:
            grade_points = 1.0
        else:
            grade_points = 0.0

        credits = score.course.credits or 1  # Default to 1 credit if not specified
        total_points += grade_points * credits
        total_credits += credits

    return round(total_points / total_credits, 2) if total_credits > 0 else 0.0


def format_student_data_for_ai(student_data):
    """
    Format student data for AI consumption

    Args:
        student_data: Student data dictionary

    Returns:
        Formatted string representation
    """
    output = []

    # Basic info
    info = student_data['student_info']
    output.append(f"Student: {info['name']} ({info['student_id']})")
    output.append(f"College: {info['college']}, Major: {info['major']}")

    # Statistics
    stats = student_data['statistics']
    output.append(f"\nACADEMIC STATISTICS:")
    output.append(f"- Total Assessments: {stats['total_scores']}")
    output.append(f"- Average Score: {stats['average_score']:.1f}")
    output.append(f"- GPA: {stats['gpa']:.2f}")
    output.append(f"- Score Range: {stats['min_score']:.1f} - {stats['max_score']:.1f}")
    output.append(f"- Recent Performance (30 days): {stats['recent_average']:.1f}")

    # Course performance
    if student_data['courses']:
        output.append(f"\nCOURSE PERFORMANCE:")
        for course in student_data['courses'][:10]:  # Limit to top 10 courses
            output.append(f"- {course['course_name']}: {course['average_score']:.1f} avg ({course['score_count']} assessments)")

    # Recent scores
    if student_data['scores']:
        output.append(f"\nRECENT SCORES:")
        # Sort by date and take last 10
        recent_scores = sorted(student_data['scores'], key=lambda x: x['date'], reverse=True)[:10]
        for score in recent_scores:
            score_date = score['date'][:10]  # Just date part
            output.append(f"- {score_date}: {score['course_name']} - {score['score']:.1f}")

    return '\n'.join(output)


def prepare_analysis_prompt(student_data, student):
    """
    Prepare analysis prompt for AI

    Args:
        student_data: Collected student data
        student: Student object

    Returns:
        Formatted prompt string
    """
    return f"""
Analyze the academic performance and learning patterns of the following student:

{format_student_data_for_ai(student_data)}

Please provide:
1. Overall academic assessment
2. Strength identification
3. Areas needing improvement
4. Specific recommendations for learning improvement
5. Teacher intervention suggestions
6. Short-term and long-term academic goals

Focus on actionable insights that can help improve the student's learning outcomes.
"""


def validate_student_data_quality(student_data):
    """
    Validate the quality and completeness of student data

    Args:
        student_data: Student data dictionary

    Returns:
        Dictionary with validation results
    """
    validation_result = {
        'is_valid': True,
        'completeness_score': 0.0,
        'data_quality_issues': [],
        'recommendations': []
    }

    # Check data completeness
    total_scores = student_data['statistics']['total_scores']

    if total_scores == 0:
        validation_result['is_valid'] = False
        validation_result['data_quality_issues'].append('No score data available')
        validation_result['completeness_score'] = 0.0
        return validation_result

    # Calculate completeness score
    if total_scores >= 20:
        validation_result['completeness_score'] = 1.0
    elif total_scores >= 10:
        validation_result['completeness_score'] = 0.8
    elif total_scores >= 5:
        validation_result['completeness_score'] = 0.6
    else:
        validation_result['completeness_score'] = 0.4
        validation_result['data_quality_issues'].append(f'Limited data: only {total_scores} assessments')

    # Check data recency
    recent_count = len([s for s in student_data['scores'] if
                       datetime.fromisoformat(s['date']) > datetime.now() - timedelta(days=90)])

    if recent_count == 0:
        validation_result['data_quality_issues'].append('No recent data (last 90 days)')
        validation_result['completeness_score'] *= 0.8
    elif recent_count < 3:
        validation_result['data_quality_issues'].append('Limited recent data')
        validation_result['completeness_score'] *= 0.9

    # Check course diversity
    course_count = len(student_data['courses'])
    if course_count < 3:
        validation_result['data_quality_issues'].append('Limited course diversity')
        validation_result['completeness_score'] *= 0.9

    # Generate recommendations
    if validation_result['completeness_score'] < 0.6:
        validation_result['recommendations'].append('Collect more assessment data before analysis')
    if recent_count < 3:
        validation_result['recommendations'].append('Update with more recent assessment results')
    if course_count < 5:
        validation_result['recommendations'].append('Include data from more courses for comprehensive analysis')

    return validation_result