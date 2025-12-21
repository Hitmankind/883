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

    # Sort courses by performance for personalized analysis
    sorted_courses = sorted(courses, key=lambda x: x.get('average_score', 0), reverse=True)
    highest_course = sorted_courses[0] if sorted_courses else None
    lowest_course = sorted_courses[-1] if sorted_courses else None

    # Generate personalized content based on actual performance
    content = f"""
# Personalized Student Learning Analysis - {student.name}

## Executive Summary
Based on the analysis of {total_scores} assessments with an average score of {avg_score:.1f}, this report provides personalized recommendations for academic improvement.

## Academic Performance Analysis

### Overall Performance
- **Average Score**: {avg_score:.1f}/100
- **Total Assessments**: {total_scores}
- **Academic Standing**: {get_academic_standing(avg_score)}
- **Performance Range**: {highest_course.get('average_score', 0):.1f} (highest) - {lowest_course.get('average_score', 0):.1f} (lowest) if highest_course and lowest_course else "N/A"

### Course Performance Breakdown
{generate_detailed_course_analysis(sorted_courses)}

## Personalized Strengths & Analysis
{generate_personalized_strengths(sorted_courses, avg_score, scores)}

## Targeted Improvement Plan
{generate_personalized_improvements(sorted_courses, avg_score, scores)}

## Customized Learning Strategy
{generate_personalized_study_strategy(sorted_courses, avg_score)}

## Specific Intervention Recommendations

{generate_specific_interventions(sorted_courses, avg_score)}

## Personalized Learning Resources
{generate_personalized_resources(sorted_courses, avg_score)}

## Action Plan & Next Steps
{generate_action_plan(sorted_courses, avg_score, student.name)}

## Confidence Assessment
**Analysis Confidence: {calculate_confidence(scores, courses):.1f}**

This analysis is personalized based on your actual academic performance data. For best results, regularly update your goals and track your progress.
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


def generate_detailed_course_analysis(sorted_courses):
    """Generate detailed course performance analysis"""
    if not sorted_courses:
        return "No course data available for analysis."

    analysis = ""
    for i, course in enumerate(sorted_courses):
        avg = course.get('average_score', 0)
        performance = get_performance_level(avg)
        rank = i + 1
        if avg >= 80:
            analysis += f"- **{rank}. {course['course_name']}**: {avg:.1f} ({performance}) ⭐ **Strength**\n"
        elif avg >= 60:
            analysis += f"- **{rank}. {course['course_name']}**: {avg:.1f} ({performance})\n"
        else:
            analysis += f"- **{rank}. {course['course_name']}**: {avg:.1f} ({performance}) ⚠️ **Needs Attention**\n"

    return analysis


def generate_personalized_strengths(sorted_courses, avg_score, scores):
    """Generate personalized strengths based on actual performance"""
    strengths = []

    # High-performing courses
    excellent_courses = [c for c in sorted_courses if c.get('average_score', 0) >= 85]
    good_courses = [c for c in sorted_courses if 75 <= c.get('average_score', 0) < 85]

    if excellent_courses:
        strengths.append(f"**Exceptional Performance** in {', '.join([c['course_name'] for c in excellent_courses])} - demonstrating mastery of complex concepts")

    if good_courses:
        strengths.append(f"**Solid Understanding** in {', '.join([c['course_name'] for c in good_courses])} - building good foundational knowledge")

    # Performance consistency analysis
    if len(sorted_courses) >= 2:
        score_variance = max([c.get('average_score', 0) for c in sorted_courses]) - min([c.get('average_score', 0) for c in sorted_courses])
        if score_variance < 15:
            strengths.append("**Consistent Performance** across all courses - showing reliable study habits")
        elif score_variance > 30:
            strengths.append("**High Potential** in specific areas - consider focusing on strengths while supporting challenging subjects")

    # Overall performance strengths
    if avg_score >= 85:
        strengths.append("**Outstanding Academic Achievement** - consistently performing at high levels")
    elif avg_score >= 75:
        strengths.append("**Strong Academic Foundation** - good performance across multiple subjects")
    elif 60 <= avg_score < 75 and scores:
        # Look for recent improvement
        recent_scores = scores[-3:] if len(scores) >= 3 else scores
        if recent_scores:
            recent_avg = sum(s['score'] for s in recent_scores) / len(recent_scores)
            if recent_avg > avg_score + 5:
                strengths.append("**Improving Trend** - recent performance shows positive momentum")

    if not strengths:
        strengths.append("Developing academic skills - with focused effort, strengths will become more apparent")

    return "\n".join(f"- {strength}" for strength in strengths)


def generate_personalized_improvements(sorted_courses, avg_score, scores):
    """Generate personalized improvement plan based on actual performance"""
    improvements = []

    # Critical courses needing immediate attention
    critical_courses = [c for c in sorted_courses if c.get('average_score', 0) < 60]
    struggling_courses = [c for c in sorted_courses if 60 <= c.get('average_score', 0) < 70]

    if critical_courses:
        improvements.append(f"**Immediate Focus Required** for {', '.join([c['course_name'] for c in critical_courses])} - scores indicate fundamental gaps in understanding")

    if struggling_courses:
        improvements.append(f"**Targeted Improvement Needed** in {', '.join([c['course_name'] for c in struggling_courses])} - additional practice and support recommended")

    # Performance gap analysis
    if len(sorted_courses) >= 2:
        highest = sorted_courses[0].get('average_score', 0)
        lowest = sorted_courses[-1].get('average_score', 0)
        gap = highest - lowest

        if gap > 25:
            improvements.append(f"**Address Performance Gap** - {gap:.1f} point difference between strongest and weakest subjects suggests inconsistent study approaches")

    # Study strategy improvements based on performance patterns
    if avg_score < 70:
        improvements.append("**Fundamental Study Skills Development** - focus on note-taking, time management, and active learning techniques")
    elif 70 <= avg_score < 80:
        improvements.append("**Advanced Study Strategies** - implement spaced repetition, practice testing, and concept mapping to elevate performance")

    # Specific recommendations based on score patterns
    if scores and len(scores) >= 3:
        recent_trend = "improving" if scores[-1]['score'] > scores[0]['score'] else "declining"
        if recent_trend == "declining":
            improvements.append("**Reverse Declining Performance** - review recent study habits and identify changes that may be affecting grades")

    return "\n".join(f"- {improvement}" for improvement in improvements)


def generate_personalized_study_strategy(sorted_courses, avg_score):
    """Generate personalized study strategy based on performance profile"""

    # Categorize courses by performance level
    high_performers = [c for c in sorted_courses if c.get('average_score', 0) >= 80]
    average_performers = [c for c in sorted_courses if 60 <= c.get('average_score', 0) < 80]
    low_performers = [c for c in sorted_courses if c.get('average_score', 0) < 60]

    strategy = ""

    if avg_score >= 80:
        strategy += """
### Advanced Excellence Strategy
- **Maintain Current Success**: Continue effective study methods
- **Challenge Yourself**: Seek advanced material and research opportunities
- **Leadership Development**: Consider peer tutoring or study group leadership
- **Goal Setting**: Aim for academic honors and competitive programs
"""
    elif 60 <= avg_score < 80:
        strategy += """
### Performance Enhancement Strategy
- **Strengthen Foundations**: Focus on core concepts in challenging courses
- **Consistent Practice**: Daily review sessions (45-60 minutes per subject)
- **Active Learning**: Transform passive reading into active problem-solving
- **Regular Assessment**: Weekly self-testing to identify knowledge gaps
"""
    else:
        strategy += """
### Academic Recovery Strategy
- **Back to Basics**: Review fundamental concepts in struggling subjects
- **Intensive Support**: Daily tutoring sessions and instructor office hours
- **Structured Schedule**: Fixed study times with minimal distractions
- **Frequent Check-ins**: Weekly progress reviews with academic advisors
"""

    # Course-specific recommendations
    if low_performers:
        strategy += f"""
### Critical Course Support
For {', '.join([c['course_name'] for c in low_performers[:2]])}:
- Schedule weekly meetings with instructors
- Form study groups with high-performing classmates
- Utilize campus tutoring services (2-3 sessions per week)
- Complete additional practice problems beyond assignments
"""

    return strategy.strip()


def generate_specific_interventions(sorted_courses, avg_score):
    """Generate specific intervention recommendations"""
    interventions = []

    lowest_courses = [c for c in sorted_courses if c.get('average_score', 0) < 70]

    if lowest_courses:
        for course in lowest_courses[:2]:  # Focus on 2 most challenging courses
            course_name = course['course_name']
            score = course.get('average_score', 0)

            if score < 50:
                interventions.append(f"**{course_name} (Score: {score:.1f})**: Immediate academic intervention required - daily tutoring, instructor meetings, and comprehensive review")
            elif 50 <= score < 60:
                interventions.append(f"**{course_name} (Score: {score:.1f})**: Intensive support needed - biweekly tutoring, study group participation, and practice exercises")
            else:
                interventions.append(f"**{course_name} (Score: {score:.1f})**: Targeted improvement - weekly review sessions, additional practice problems")

    if not interventions:
        interventions.append("Continue current successful approach while monitoring for any emerging challenges")

    return "\n".join(f"- {intervention}" for intervention in interventions)


def generate_personalized_resources(sorted_courses, avg_score):
    """Generate personalized learning resources based on actual performance"""

    # Identify subject areas based on course names
    math_courses = [c for c in sorted_courses if any(keyword in c['course_name'].lower() for keyword in ['数学', 'math', '代数', 'algebra', '微积分', 'calculus'])]
    cs_courses = [c for c in sorted_courses if any(keyword in c['course_name'].lower() for keyword in ['计算机', 'computer', '网络', 'network', '数据结构', 'data structure', '编程', 'programming'])]
    english_courses = [c for c in sorted_courses if any(keyword in c['course_name'].lower() for keyword in ['英语', 'english', '语言', 'language'])]

    resources = []

    # Prioritize resources based on performance needs
    low_performing_courses = [c for c in sorted_courses if c.get('average_score', 0) < 70]

    if math_courses and any(c in low_performing_courses for c in math_courses):
        resources.append("""
### Mathematics Support (Priority - Based on Performance)
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
""")

    if cs_courses and any(c in low_performing_courses for c in cs_courses):
        resources.append("""
### Computer Science Support (Priority - Based on Performance)
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
""")

    if avg_score < 70:
        resources.append("""
### Study Skills & Academic Success
<div style="margin: 10px 0;">
    <button onclick="window.open('https://www.youtube.com/user/einfachtom', '_blank')" style="background: #FF0000; color: white; border: none; padding: 8px 16px; margin: 5px; border-radius: 4px; cursor: pointer;">
        📚 Thomas Frank - Study Skills
    </button>
    <button onclick="window.open('https://www.youtube.com/c/MarianasStudyCorner', '_blank')" style="background: #FF0000; color: white; border: none; padding: 8px 16px; margin: 5px; border-radius: 4px; cursor: pointer;">
        ✏️ Mariana's Study Corner
    </button>
</div>
""")

    if not resources:
        resources.append("""
### General Academic Resources
<div style="margin: 10px 0;">
    <button onclick="window.open('https://www.youtube.com/c/crashcourse', '_blank')" style="background: #FF0000; color: white; border: none; padding: 8px 16px; margin: 5px; border-radius: 4px; cursor: pointer;">
        🎬 Crash Course
    </button>
</div>
""")

    return "".join(resources)


def generate_action_plan(sorted_courses, avg_score, student_name):
    """Generate personalized action plan"""

    # Identify priority courses
    priority_courses = [c for c in sorted_courses if c.get('average_score', 0) < 70]

    if avg_score < 60:
        return f"""
### Immediate Action Plan for {student_name}

**Week 1-2: Foundation Building**
1. Schedule meetings with all course instructors
2. Join study groups for {', '.join([c['course_name'] for c in priority_courses[:2]])}
3. Establish daily study routine (minimum 2 hours per day)
4. Complete all missing assignments

**Week 3-4: Skill Development**
1. Attend tutoring sessions 3 times per week
2. Practice additional problems beyond homework
3. Form accountability partnerships with classmates
4. Weekly progress review with academic advisor

**Ongoing:**
- Daily review sessions (30 minutes per course)
- Weekly self-assessment and goal adjustment
- Regular instructor check-ins
"""
    elif 60 <= avg_score < 75:
        return f"""
### Improvement Action Plan for {student_name}

**Short-term Goals (Next 2 weeks)**
1. Focus extra study time on {', '.join([c['course_name'] for c in priority_courses])}
2. Form or join study groups for challenging courses
3. Schedule instructor office hours for concept clarification
4. Implement active study techniques (practice testing, concept mapping)

**Mid-term Goals (This semester)**
1. Achieve minimum 75 in all current courses
2. Develop consistent study schedule
3. Improve time management skills
4. Build stronger peer learning networks
"""
    else:
        return f"""
### Excellence Action Plan for {student_name}

**Goals for Continued Success**
1. Maintain current high performance standards
2. Seek advanced learning opportunities
3. Consider leadership roles in study groups
4. Explore research or internship opportunities in your strongest areas

**Stretch Goals**
1. Achieve Dean's List recognition
2. Participate in academic competitions
3. Develop mentorship skills to help peers
4. Pursue independent study projects
"""


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