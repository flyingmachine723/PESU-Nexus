import json
from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse

from .models import Question, Mock_Test, Test_Attempt, Answer


def _format_duration(td):
    """Format a timedelta to a human string with seconds precision."""
    if td is None:
        return None

    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


@login_required
def mocktest_view(request):
    # All semesters that actually have at least one test
    semesters = list(
        Mock_Test.objects
        .values_list('semester', flat=True)
        .distinct()
        .order_by('semester')
    )

    # Build mapping: { 1: ["B.Tech CSE", "B.Tech ECE"], 2: [...] }
    courses_by_sem = {}
    for sem in semesters:
        courses_by_sem[sem] = list(
            Mock_Test.objects
            .filter(semester=sem)
            .values_list('course_name', flat=True)
            .distinct()
            .order_by('course_name')
        )

    all_courses = list(
        Mock_Test.objects
        .values_list('course_name', flat=True)
        .distinct()
        .order_by('course_name')
    )

    return render(
        request,
        'mocktests/mocktest.html',
        {
            'semesters': semesters,
            'courses_by_sem_json': courses_by_sem,
            'all_courses': all_courses,
        }
    )


@login_required
def test_selection_view(request):
    if request.method == 'POST':
        semester = request.POST.get('semester')
        course = request.POST.get('course')

        tests = Mock_Test.objects.filter(
            semester=semester,
            course_name=course
        )

        return render(
            request,
            'mocktests/test_selection.html',
            {
                'tests': tests
            }
        )

    return redirect('mocktests:mock_tests')


@login_required
def take_test_view(request, test_id):
    test = get_object_or_404(Mock_Test, id=test_id)
    now = timezone.now()

    questions = test.questions.all()

    attempt = Test_Attempt.objects.filter(
        user=request.user,
        test=test,
        completed_at__isnull=True
    ).order_by('-started_at').first()

    if attempt is not None:
        deadline = attempt.started_at + timedelta(minutes=test.duration)
        if now >= deadline:
            attempt.completed_at = now
            attempt.score = 0
            attempt.save()
            attempt = None

    if attempt is None:
        attempt = Test_Attempt.objects.create(
            user=request.user,
            test=test
        )

    deadline = attempt.started_at + timedelta(minutes=test.duration)

    questions_data = []
    for question in questions:
        questions_data.append({
            'id': question.id,
            'question_desc': question.question_desc,
            'question_image': question.question_image.url if question.question_image else None,
            'option_a': question.option_a,
            'option_b': question.option_b,
            'option_c': question.option_c,
            'option_d': question.option_d,
        })

    return render(
        request,
        'mocktests/take_test.html',
        {
            'test': test,
            'questions_data': questions_data,
            'attempt': attempt,
            'deadline': deadline.timestamp() * 1000,
        }
    )


@login_required
def submit_test_view(request):
    if request.method != 'POST':
        return JsonResponse(
            {'success': False, 'message': 'Invalid request method.'},
            status=405
        )

    attempt_id = request.POST.get('attempt_id')

    if not attempt_id:
        return JsonResponse(
            {'success': False, 'message': 'Attempt ID is required.'},
            status=400
        )

    attempt = get_object_or_404(
        Test_Attempt,
        id=attempt_id,
        user=request.user
    )

    if attempt.completed_at is not None:
        return JsonResponse({
            'success': True,
            'already_submitted': True,
            'redirect_url': f'/mocktests/analysis/{attempt.id}/'
        })

    deadline = attempt.started_at + timedelta(
        minutes=attempt.test.duration
    )
    now = timezone.now()

    answers = request.POST.get('answers')

    if not answers:
        answers = {}
    else:
        try:
            answers = json.loads(answers)
        except json.JSONDecodeError:
            return JsonResponse(
                {'success': False, 'message': 'Invalid answer data.'},
                status=400
            )

        if not isinstance(answers, dict):
            return JsonResponse(
                {'success': False, 'message': 'Invalid answer format.'},
                status=400
            )

    # ============================================================
    # FAST PATH — batch all DB operations into ~4 queries
    # ============================================================

    question_ids = []
    for qid in answers.keys():
        try:
            question_ids.append(int(qid))
        except (TypeError, ValueError):
            continue

    questions_by_id = Question.objects.filter(
        id__in=question_ids,
        test=attempt.test
    ).in_bulk()

    existing_answers = {
        ans.question_id: ans
        for ans in Answer.objects.filter(attempt=attempt)
    }

    to_create = []
    to_update = []
    score = 0

    for question_id_str, selected_answer in answers.items():
        try:
            qid = int(question_id_str)
        except (TypeError, ValueError):
            continue

        question = questions_by_id.get(qid)
        if question is None:
            continue

        if selected_answer.lower() == question.correct_answer.lower():
            score += question.marks

        existing = existing_answers.get(qid)
        if existing is not None:
            existing.selected_answer = selected_answer
            to_update.append(existing)
        else:
            to_create.append(Answer(
                attempt=attempt,
                question=question,
                selected_answer=selected_answer,
            ))

    with transaction.atomic():
        if to_create:
            Answer.objects.bulk_create(to_create, batch_size=500)
        if to_update:
            Answer.objects.bulk_update(
                to_update,
                ['selected_answer'],
                batch_size=500,
            )

        attempt.score = score
        attempt.completed_at = now
        attempt.save(update_fields=['score', 'completed_at'])

    expired = now >= deadline

    return JsonResponse({
        'success': True,
        'score': score,
        'expired': expired,
        'redirect_url': f'/mocktests/analysis/{attempt.id}/'
    })


@login_required
def test_analysis_view(request, attempt_id):
    attempt = get_object_or_404(
        Test_Attempt,
        id=attempt_id,
        user=request.user,
        completed_at__isnull=False
    )

    questions = attempt.test.questions.all()

    selected_map = {
        ans.question_id: ans.selected_answer
        for ans in attempt.answers.all()
    }

    total_marks = sum(q.marks for q in questions)

    correct_count = 0
    wrong_count = 0
    unattempted_count = 0

    for q in questions:
        selected = selected_map.get(q.id)

        if selected is None:
            unattempted_count += 1
        elif selected.lower() == q.correct_answer.lower():
            correct_count += 1
        else:
            wrong_count += 1

    total_questions = questions.count()

    attempted_count = correct_count + wrong_count

    accuracy = 0
    if attempted_count > 0:
        accuracy = round((correct_count / attempted_count) * 100, 2)

    percentage = 0
    if total_marks > 0:
        percentage = round((attempt.score / total_marks) * 100, 2)

    time_taken = None
    if attempt.completed_at:
        time_taken = _format_duration(attempt.completed_at - attempt.started_at)

    # Rank + average among unique users (first attempt per user, tie by time)
    first_attempts = _first_attempts_for_test(attempt.test)

    rank = None
    for idx, entry in enumerate(first_attempts, start=1):
        if entry['user_id'] == attempt.user_id:
            rank = idx
            break

    if rank is None:
        rank = len(first_attempts) + 1

    total_attempts = len(first_attempts)

    average_score = 0
    if total_attempts > 0 and total_marks > 0:
        total_score_sum = sum(entry['score'] for entry in first_attempts)
        average_score = round(
            (total_score_sum / total_attempts / total_marks) * 100, 1
        )

    response = render(
        request,
        'mocktests/test_analysis.html',
        {
            'attempt': attempt,
            'test': attempt.test,
            'score': attempt.score,
            'total_marks': total_marks,
            'percentage': percentage,
            'correct_count': correct_count,
            'wrong_count': wrong_count,
            'unattempted_count': unattempted_count,
            'total_questions': total_questions,
            'accuracy': accuracy,
            'time_taken': time_taken,
            'rank': rank,
            'total_attempts': total_attempts,
            'average_score': average_score,
        }
    )
    response['Cache-Control'] = 'no-store'
    return response


@login_required
def test_questions_view(request, attempt_id):
    attempt = get_object_or_404(
        Test_Attempt,
        id=attempt_id,
        user=request.user,
        completed_at__isnull=False
    )

    questions = attempt.test.questions.all()

    selected_map = {
        ans.question_id: ans.selected_answer
        for ans in attempt.answers.all()
    }

    review_data = []

    for q in questions:
        selected = selected_map.get(q.id)
        is_correct = (
            selected is not None
            and selected.lower() == q.correct_answer.lower()
        )

        review_data.append({
            'id': q.id,
            'question_desc': q.question_desc,
            'question_image': q.question_image.url if q.question_image else None,
            'option_a': q.option_a,
            'option_b': q.option_b,
            'option_c': q.option_c,
            'option_d': q.option_d,
            'selected': selected,
            'correct_answer': q.correct_answer,
            'is_correct': is_correct,
            'marks': q.marks,
            'explanation': q.explanation or '',
        })

    response = render(
        request,
        'mocktests/test_questions.html',
        {
            'attempt': attempt,
            'test': attempt.test,
            'review_data': review_data,
        }
    )
    response['Cache-Control'] = 'no-store'
    return response


def _first_attempts_for_test(test):
    """
    Return a sorted list of first-attempts (one per user) for a test.
    """

    all_attempts = (
        Test_Attempt.objects
        .filter(test=test, completed_at__isnull=False)
        .select_related('user')
        .order_by('user_id', 'started_at')
    )

    first_by_user = {}
    for a in all_attempts:
        if a.user_id not in first_by_user:
            first_by_user[a.user_id] = a

    total_marks = sum(q.marks for q in test.questions.all())

    entries = []
    for a in first_by_user.values():
        delta = a.completed_at - a.started_at
        seconds = int(delta.total_seconds())

        entries.append({
            'user_id': a.user_id,
            'username': a.user.username,
            'attempt': a,
            'score': a.score,
            'time_taken': _format_duration(delta),
            'time_taken_seconds': seconds,
            'total_marks': total_marks,
        })

    entries.sort(key=lambda e: (-e['score'], e['time_taken_seconds']))

    return entries


@login_required
def test_leaderboard_view(request, attempt_id):
    attempt = get_object_or_404(
        Test_Attempt,
        id=attempt_id,
        user=request.user,
        completed_at__isnull=False
    )

    test = attempt.test

    entries = _first_attempts_for_test(test)

    total_marks = entries[0]['total_marks'] if entries else 0

    for idx, entry in enumerate(entries, start=1):
        entry['rank'] = idx

    top_20 = entries[:20]

    current_user_entry = None
    for entry in entries:
        if entry['user_id'] == request.user.id:
            current_user_entry = entry
            break

    current_user_in_top = (
        current_user_entry is not None
        and current_user_entry['rank'] <= 20
    )

    chart_top = top_20[:10]
    lb_chart_labels = json.dumps([e['username'] for e in chart_top])
    lb_chart_scores = json.dumps([
        round(e['score'] / e['total_marks'] * 100, 1) if e['total_marks'] else 0
        for e in chart_top
    ])
    lb_chart_raw = json.dumps([e['score'] for e in chart_top])

    buckets = [0, 0, 0, 0, 0]
    for e in entries:
        pct = (e['score'] / e['total_marks'] * 100) if e['total_marks'] else 0
        idx = min(int(pct // 20), 4)
        buckets[idx] += 1
    dist_labels = json.dumps(['0–20%', '21–40%', '41–60%', '61–80%', '81–100%'])
    dist_data = json.dumps(buckets)

    return render(
        request,
        'mocktests/test_leaderboard.html',
        {
            'attempt': attempt,
            'test': test,
            'entries': top_20,
            'total_marks': total_marks,
            'current_user_entry': current_user_entry,
            'current_user_in_top': current_user_in_top,
            'total_participants': len(entries),
            'lb_chart_labels': lb_chart_labels,
            'lb_chart_scores': lb_chart_scores,
            'lb_chart_raw': lb_chart_raw,
            'dist_labels': dist_labels,
            'dist_data': dist_data,
        }
    )


@login_required
def attempt_history_view(request):
    completed_attempts = (
        Test_Attempt.objects
        .filter(user=request.user, completed_at__isnull=False)
        .select_related('test')
        .order_by('-completed_at')
    )

    seen_tests = set()
    latest_per_test = []

    for attempt in completed_attempts:
        if attempt.test_id in seen_tests:
            continue
        seen_tests.add(attempt.test_id)

        total_marks = sum(
            q.marks for q in attempt.test.questions.all()
        )

        questions = attempt.test.questions.all()
        selected_map = {
            ans.question_id: ans.selected_answer
            for ans in attempt.answers.all()
        }
        correct = wrong = skipped = 0
        for q in questions:
            sel = selected_map.get(q.id)
            if sel is None:
                skipped += 1
            elif sel.lower() == q.correct_answer.lower():
                correct += 1
            else:
                wrong += 1

        pct = round((attempt.score / total_marks * 100), 1) if total_marks else 0

        latest_per_test.append({
            'attempt': attempt,
            'test': attempt.test,
            'score': attempt.score,
            'total_marks': total_marks,
            'percentage': pct,
            'correct': correct,
            'wrong': wrong,
            'skipped': skipped,
            'completed_at': attempt.completed_at,
            'time_taken': _format_duration(
                attempt.completed_at - attempt.started_at
            ),
        })

    chart_entries = list(reversed(latest_per_test))
    chart_labels = [e['test'].title[:20] for e in chart_entries]
    chart_scores = [e['percentage'] for e in chart_entries]
    chart_correct = [e['correct'] for e in chart_entries]
    chart_wrong = [e['wrong'] for e in chart_entries]
    chart_skipped = [e['skipped'] for e in chart_entries]

    total_tests = len(latest_per_test)
    avg_score = round(sum(chart_scores) / total_tests, 1) if total_tests else 0
    best_score = max(chart_scores) if chart_scores else 0

    response = render(
        request,
        'mocktests/attempt_history.html',
        {
            'entries': latest_per_test,
            'chart_labels': json.dumps(chart_labels),
            'chart_scores': json.dumps(chart_scores),
            'chart_correct': json.dumps(chart_correct),
            'chart_wrong': json.dumps(chart_wrong),
            'chart_skipped': json.dumps(chart_skipped),
            'total_tests': total_tests,
            'avg_score': avg_score,
            'best_score': best_score,
        }
    )
    response['Cache-Control'] = 'no-store'
    return response