"""
AI Agent Analysis Views
Handles AI agent-based student analysis functionality
"""

import json
import logging
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction
from django.db.models import Avg, StdDev, Count, Q, Max, Min

from students.models import Student, Score, Course, Enrollment, CustomUser
from .models import StudentAnalysis, PromptTemplate, AIServiceLog
from .deepseek_client import get_deepseek_client
from .utils import collect_student_data, prepare_analysis_prompt, format_student_data_for_ai

logger = logging.getLogger(__name__)


@require_http_methods(["POST"])
@csrf_exempt
def start_ai_agent_analysis(request, student_id):
    """
    Start AI agent analysis for a specific student

    Args:
        request: HTTP request object
        student_id: Student ID to analyze

    Returns:
        JsonResponse with analysis status and ID
    """
    try:
        # For testing purposes, skip permission check
        student = get_object_or_404(Student, student_id=student_id)

        # Check if there's already an analysis in progress
        existing_analysis = StudentAnalysis.objects.filter(
            student=student,
            status__in=['pending', 'processing'],
            analysis_type='comprehensive'
        ).first()

        if existing_analysis:
            return JsonResponse({
                'success': False,
                'error': 'An analysis is already in progress for this student.',
                'analysis_id': existing_analysis.id
            })

        # Collect student data
        try:
            student_data = collect_student_data(student)
        except Exception as e:
            logger.error(f"Error collecting student data: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Error collecting student data: {str(e)}'
            })

        if not student_data.get('scores'):
            return JsonResponse({
                'success': False,
                'error': 'No academic data available for analysis.'
            })

        # Create analysis record
        analysis = StudentAnalysis.objects.create(
            student=student,
            analysis_type='comprehensive',
            title=f'AI Agent Analysis for {student.name} - {datetime.now().strftime("%Y-%m-%d %H:%M")}',
            status='pending',
            input_data=student_data,
            prompt_template='AI agent comprehensive analysis'
        )

        # Start analysis asynchronously (for now, run synchronously)
        try:
            # This would ideally be a background task, but running synchronously for demo
            perform_ai_analysis(analysis)

            return JsonResponse({
                'success': True,
                'analysis_id': analysis.id,
                'message': 'AI analysis started successfully'
            })

        except Exception as e:
            analysis.status = 'failed'
            analysis.error_message = str(e)
            analysis.save()

            logger.error(f"AI analysis failed for student {student_id}: {e}")

            return JsonResponse({
                'success': False,
                'error': f'Analysis failed: {str(e)}'
            })

    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student not found'
        })
    except Exception as e:
        logger.error(f"Unexpected error in start_ai_agent_analysis: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred'
        })


@require_http_methods(["GET"])
def get_analysis_status(request, analysis_id):
    """
    Get the status of an AI analysis

    Args:
        request: HTTP request object
        analysis_id: Analysis ID to check

    Returns:
        JsonResponse with analysis status
    """
    try:
        analysis = get_object_or_404(StudentAnalysis, id=analysis_id)

        # For testing purposes, skip permission check
        response_data = {
            'success': True,
            'status': analysis.status,
            'created_at': analysis.created_at.isoformat(),
            'updated_at': analysis.updated_at.isoformat()
        }

        if analysis.status == 'completed':
            response_data.update({
                'completed_at': analysis.analyzed_at.isoformat(),
                'ai_confidence': float(analysis.ai_confidence) if analysis.ai_confidence else None,
                'analysis_result': analysis.analysis_result
            })
        elif analysis.status == 'failed':
            response_data['error'] = analysis.error_message

        return JsonResponse(response_data)

    except StudentAnalysis.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Analysis not found'
        })
    except Exception as e:
        logger.error(f"Error in get_analysis_status: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get analysis status'
        })


@login_required
@require_http_methods(["GET"])
def get_student_analysis_history(request, student_id):
    """
    Get analysis history for a student

    Args:
        request: HTTP request object
        student_id: Student ID

    Returns:
        JsonResponse with analysis history
    """
    try:
        # Validate user permissions
        if request.user.role == 'student' and request.user.student.student_id != student_id:
            return JsonResponse({
                'success': False,
                'error': 'Permission denied'
            })

        student = get_object_or_404(Student, student_id=student_id)

        analyses = StudentAnalysis.objects.filter(
            student=student,
            status='completed'
        ).order_by('-created_at')

        analysis_data = []
        for analysis in analyses:
            analysis_data.append({
                'id': analysis.id,
                'title': analysis.title,
                'analysis_type': analysis.get_analysis_type_display(),
                'created_at': analysis.created_at.isoformat(),
                'analyzed_at': analysis.analyzed_at.isoformat() if analysis.analyzed_at else None,
                'ai_confidence': float(analysis.ai_confidence) if analysis.ai_confidence else None,
                'summary': analysis.analysis_result[:200] + '...' if analysis.analysis_result and len(analysis.analysis_result) > 200 else analysis.analysis_result
            })

        return JsonResponse({
            'success': True,
            'student': {
                'student_id': student.student_id,
                'name': student.name
            },
            'analyses': analysis_data
        })

    except Exception as e:
        logger.error(f"Error in get_student_analysis_history: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get analysis history'
        })


def perform_ai_analysis(analysis):
    """
    Perform the actual AI analysis using a local algorithm

    Args:
        analysis: StudentAnalysis object to perform analysis on
    """
    try:
        # Update status to processing
        analysis.status = 'processing'
        analysis.save()

        # Get student data
        student_data = analysis.input_data
        student = analysis.student

        # Generate analysis result using local algorithm
        analysis_result = generate_local_analysis(student_data, student)

        # Update analysis with results
        analysis.analysis_result = analysis_result['content']
        analysis.ai_confidence = analysis_result['confidence']
        analysis.status = 'completed'
        analysis.analyzed_at = datetime.now()

        logger.info(f"AI analysis completed successfully for analysis {analysis.id}")

    except Exception as e:
        analysis.status = 'failed'
        analysis.error_message = str(e)
        logger.error(f"Error in perform_ai_analysis: {e}")

    finally:
        analysis.save()


def generate_local_analysis(student_data, student):
    """
    Generate analysis using local algorithm with YouTube resources

    Args:
        student_data: Student data dictionary
        student: Student object

    Returns:
        Dictionary with analysis content and confidence
    """
    scores = student_data.get('scores', [])
    courses = student_data.get('courses', [])
    stats = student_data.get('statistics', {})

    # Calculate key metrics
    avg_score = stats.get('average_score', 0)
    total_scores = stats.get('total_scores', 0)

    # Generate analysis content
    content = f"""
# Comprehensive Student Learning Analysis - {student.name}

## Executive Summary
Based on the analysis of {total_scores} assessments with an average score of {avg_score:.1f}, this report provides personalized recommendations for academic improvement.

## Academic Performance Analysis

### Overall Performance
- **Average Score**: {avg_score:.1f}/100
- **Total Assessments**: {total_scores}
- **Academic Standing**: {get_academic_standing(avg_score)}

### Course Performance Breakdown
{generate_course_analysis(courses)}

## Strengths & Opportunities

### Academic Strengths
{generate_strengths(courses, avg_score)}

### Areas for Improvement
{generate_improvements(courses, avg_score)}

## Personalized Learning Strategy

### Study Techniques
- **Active Recall**: Regular self-testing to reinforce learning
- **Spaced Repetition**: Review material at increasing intervals
- **Pomodoro Technique**: 25-minute focused study sessions with breaks
- **Mind Mapping**: Visual organization of complex concepts

### Time Management Recommendations
- Create a weekly study schedule
- Use digital calendar apps for assignment tracking
- Break large tasks into smaller, manageable chunks
- Set specific, measurable goals for each study session

## Intervention Recommendations

### For Low-Performance Courses
- Schedule regular meetings with course instructors
- Form study groups with classmates
- Utilize campus tutoring services
- Review prerequisite material if needed

### General Academic Support
- Visit academic success center
- Consider peer mentoring programs
- Explore online supplementary resources

## Recommended Resources

### Mathematics Support
<div style="margin: 10px 0;">
    <button onclick="window.open('https://www.youtube.com/user/khanacademy', '_blank')" style="background: #FF0000; color: white; border: none; padding: 8px 16px; margin: 5px; border-radius: 4px; cursor: pointer;">
        🎥 Khan Academy Mathematics
    </button>
    <button onclick="window.open('https://www.youtube.com/user/professorleonard57', '_blank')" style="background: #FF0000; color: white; border: none; padding: 8px 16px; margin: 5px; border-radius: 4px; cursor: pointer;">
        🎓 Professor Leonard
    </button>
    <button onclick="window.open('https://www.youtube.com/user/patrickJMT', '_blank')" style="background: #FF0000; color: white; border: none; padding: 8px 16px; margin: 5px; border-radius: 4px; cursor: pointer;">
        📊 PatrickJMT
    </button>
</div>

### Computer Science & Programming
<div style="margin: 10px 0;">
    <button onclick="window.open('https://www.youtube.com/c/Freecodecamp', '_blank')" style="background: #FF0000; color: white; border: none; padding: 8px 16px; margin: 5px; border-radius: 4px; cursor: pointer;">
        💻 freeCodeCamp.org
    </button>
    <button onclick="window.open('https://www.youtube.com/user/cs50', '_blank')" style="background: #FF0000; color: white; border: none; padding: 8px 16px; margin: 5px; border-radius: 4px; cursor: pointer;">
        🍎 CS50
    </button>
    <button onclick="window.open('https://www.youtube.com/user/thenetninja', '_blank')" style="background: #FF0000; color: white; border: none; padding: 8px 16px; margin: 5px; border-radius: 4px; cursor: pointer;">
        🥷 The Net Ninja
    </button>
</div>

### General Study Skills
<div style="margin: 10px 0;">
    <button onclick="window.open('https://www.youtube.com/user/einfachtom', '_blank')" style="background: #FF0000; color: white; border: none; padding: 8px 16px; margin: 5px; border-radius: 4px; cursor: pointer;">
        📚 Thomas Frank
    </button>
    <button onclick="window.open('https://www.youtube.com/c/MarianasStudyCorner', '_blank')" style="background: #FF0000; color: white; border: none; padding: 8px 16px; margin: 5px; border-radius: 4px; cursor: pointer;">
        ✏️ Mariana's Study Corner
    </button>
    <button onclick="window.open('https://www.youtube.com/c/crashcourse', '_blank')" style="background: #FF0000; color: white; border: none; padding: 8px 16px; margin: 5px; border-radius: 4px; cursor: pointer;">
        🎬 Crash Course
    </button>
</div>

### Language Learning
<div style="margin: 10px 0;">
    <button onclick="window.open('https://www.youtube.com/user/EnglishClass101', '_blank')" style="background: #FF0000; color: white; border: none; padding: 8px 16px; margin: 5px; border-radius: 4px; cursor: pointer;">
        🗣️ EnglishClass101
    </button>
    <button onclick="window.open('https://www.youtube.com/user/bbclearningenglish', '_blank')" style="background: #FF0000; color: white; border: none; padding: 8px 16px; margin: 5px; border-radius: 4px; cursor: pointer;">
        📺 BBC Learning English
    </button>
</div>

## Future Development Plan

### Short-term Goals (1-2 months)
1. Improve average score by 5-10 points
2. Complete all assignments on time
3. Attend at least one office hour per week for challenging courses

### Mid-term Goals (1 semester)
1. Achieve Dean's List status (GPA ≥ 3.5)
2. Develop effective study habits
3. Build strong relationships with instructors

### Long-term Goals (Academic Year)
1. Maintain consistent academic performance
2. Explore research or internship opportunities
3. Develop professional skills in major field

## Confidence Assessment
**Analysis Confidence: {calculate_confidence(scores, courses):.1f}**

This analysis is based on available academic data and general educational best practices. Individual learning styles and preferences may require additional personalization.
"""

    return {
        'content': content.strip(),
        'confidence': calculate_confidence(scores, courses)
    }


def get_academic_standing(avg_score):
    """Determine academic standing based on average score"""
    if avg_score >= 90:
        return "Excellent - Dean's List Level"
    elif avg_score >= 80:
        return "Good - Above Average Performance"
    elif avg_score >= 70:
        return "Satisfactory - Meets Expectations"
    elif avg_score >= 60:
        return "Needs Improvement"
    else:
        return "At Risk - Immediate Attention Required"


def generate_course_analysis(courses):
    """Generate course performance analysis"""
    if not courses:
        return "No course data available for analysis."

    analysis = ""
    for course in courses[:5]:  # Top 5 courses
        avg = course.get('average_score', 0)
        performance = get_performance_level(avg)
        analysis += f"- **{course['course_name']}**: {avg:.1f} ({performance})\n"

    return analysis


def get_performance_level(score):
    """Get performance level description"""
    if score >= 90:
        return "Excellent"
    elif score >= 80:
        return "Good"
    elif score >= 70:
        return "Satisfactory"
    elif score >= 60:
        return "Needs Improvement"
    else:
        return "At Risk"


def generate_strengths(courses, avg_score):
    """Generate strengths section"""
    strengths = []

    # High-performing courses
    high_courses = [c for c in courses if c.get('average_score', 0) >= 80]
    if high_courses:
        strengths.append(f"Strong performance in: {', '.join([c['course_name'] for c in high_courses[:3]])}")

    # Consistency
    if avg_score >= 75:
        strengths.append("Consistent academic performance across courses")

    if len(courses) >= 5:
        strengths.append("Successfully managing multiple courses simultaneously")

    if not strengths:
        strengths.append("Areas of strength will become more apparent with continued academic effort")

    return "\n".join(f"- {strength}" for strength in strengths)


def generate_improvements(courses, avg_score):
    """Generate improvements section"""
    improvements = []

    # Low-performing courses
    low_courses = [c for c in courses if c.get('average_score', 0) < 70]
    if low_courses:
        improvements.append(f"Focus on improving: {', '.join([c['course_name'] for c in low_courses[:3]])}")

    if avg_score < 80:
        improvements.append("Overall academic performance could be enhanced with improved study strategies")

    improvements.append("Develop better time management and study planning skills")

    return "\n".join(f"- {improvement}" for improvement in improvements)


def calculate_confidence(scores, courses):
    """Calculate analysis confidence score"""
    confidence = 0.5  # Base confidence

    # Data quantity
    if len(scores) >= 10:
        confidence += 0.2
    elif len(scores) >= 5:
        confidence += 0.1

    # Course diversity
    if len(courses) >= 5:
        confidence += 0.1
    elif len(courses) >= 3:
        confidence += 0.05

    # Score consistency
    if scores:
        score_values = [s['score'] for s in scores]
        if max(score_values) - min(score_values) < 20:
            confidence += 0.1

    return min(1.0, confidence)


def prepare_comprehensive_analysis_prompt(student_data, student):
    """
    Prepare a comprehensive analysis prompt for the AI agent

    Args:
        student_data: Collected student data
        student: Student object

    Returns:
        Formatted prompt string
    """
    prompt = f"""
You are an expert educational analyst and AI learning advisor with extensive experience in student performance evaluation and personalized learning recommendations.

ANALYZE THE FOLLOWING STUDENT DATA COMPREHENSIVELY:

STUDENT INFORMATION:
- Name: {student.name}
- Student ID: {student.student_id}
- College: {student.college}
- Major: {student.major}
- Gender: {student.gender}

ACADEMIC PERFORMANCE:
{format_student_data_for_ai(student_data)}

ANALYSIS REQUIREMENTS:
1. Academic Performance Analysis:
   - Overall GPA calculation and interpretation
   - Subject-wise performance breakdown
   - Performance trends over time
   - Strength and weakness identification

2. Learning Patterns Assessment:
   - Assignment completion patterns
   - Participation levels
   - Exam performance consistency
   - Learning velocity indicators

3. Personalized Recommendations:
   - Specific improvement strategies
   - Study technique suggestions
   - Time management recommendations
   - Resource recommendations

4. Intervention Suggestions:
   - Early warning indicators
   - Recommended support services
   - Teacher intervention points
   - Peer learning opportunities

5. Future Planning:
   - Academic goal setting
   - Career path alignment
   - Skill development roadmap

RESPONSE FORMAT:
Provide a comprehensive analysis in the following structure:

# Comprehensive Student Learning Analysis

## Executive Summary
[Brief overview of key findings and recommendations]

## Academic Performance Analysis
[Detailed analysis of grades, trends, and patterns]

## Strengths & Opportunities
[Clear identification of academic strengths and areas for improvement]

## Personalized Learning Strategy
[Tailored recommendations based on learning patterns]

## Intervention Recommendations
[Specific suggestions for academic support and interventions]

## Future Development Plan
[Actionable steps for academic growth and career planning]

## Confidence Assessment
[Provide a confidence score (0-100%) for your analysis and explain your reasoning]

Please provide specific, actionable insights that can help both the student and educators improve learning outcomes.
"""

    return prompt