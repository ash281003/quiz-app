from urllib import request

from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Category
from .models import Quiz
from django.shortcuts import get_object_or_404
from .models import Quiz, Question
from .models import Option
from .models import Attempt, Answer
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count

def category_quizzes(request, category_id):
    quizzes = Quiz.objects.filter(category_id=category_id)
    return render(request, 'core/quizzes_by_category.html', {'quizzes': quizzes})

@staff_member_required
def admin_dashboard(request):
    from .models import User, Quiz, Attempt

    context = {
        'total_users': User.objects.count(),
        'total_quizzes': Quiz.objects.count(),
        'total_attempts': Attempt.objects.count(),
        'top_quizzes': Quiz.objects.annotate(attempts=Count('attempt')).order_by('-attempts')[:5],
    }

    return render(request, 'core/admin_dashboard.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome {username}!")
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('login')

    return render(request, 'core/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email    = request.POST['email']
        password = request.POST['password']
        confirm  = request.POST['confirm_password']

        # Validate form
        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('register')

        # Save user
        User.objects.create(
            username=username,
            email=email,
            password=make_password(password)
        )

        messages.success(request, "Account created successfully. Please login.")
        return redirect('login')

    return render(request, 'core/register.html')

def home(request):
    categories = Category.objects.all()
    return render(request, 'core/home.html', {'categories': categories})

def start_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    questions = quiz.question_set.all()

    # Start at question 0
    request.session['quiz_id'] = quiz_id
    request.session['question_index'] = 0
    request.session['score'] = 0
    request.session['answers'] = {}

    return redirect('attempt_quiz')

def attempt_quiz(request):
    quiz_id = request.session.get('quiz_id')
    question_index = request.session.get('question_index', 0)
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    questions = quiz.question_set.all()

    if question_index >= len(questions):
        return redirect('quiz_result')

    current_question = questions[question_index]
    options = current_question.options.all()

    if request.method == 'POST':
        selected_option_id = request.POST.get('option')
        if selected_option_id:
            selected_option = Option.objects.get(id=selected_option_id)
            # Store user's answer
            request.session['answers'][str(current_question.id)] = selected_option.id
            # Update score
            if selected_option.is_correct:
                request.session['score'] += 1

        # Move to next question
        request.session['question_index'] += 1
        return redirect('attempt_quiz')

    return render(request, 'core/quiz_attempt.html', {
        'question': current_question,
        'options': options,
        'question_number': question_index + 1,
        'total_questions': len(questions),
    })

def quiz_result(request):
    score = request.session.get('score', 0)
    quiz_id = request.session.get('quiz_id')
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    total_questions = quiz.question_set.count()
    answers = request.session.get('answers', {})

    # Save attempt
    attempt = Attempt.objects.create(
        user=request.user,
        quiz=quiz,
        score=score,
        total=total_questions,
    )

    # Save each answer
    for qid, oid in answers.items():
        question = Question.objects.get(pk=qid)
        option = Option.objects.get(pk=oid)
        Answer.objects.create(
            attempt=attempt,
            question=question,
            selected_option=option
        )

    # Clear session
    for key in ['score', 'quiz_id', 'question_index', 'answers']:
        request.session.pop(key, None)

    return render(request, 'core/quiz_result.html', {
        'score': score,
        'total_questions': total_questions,
        'quiz': quiz
    })

def my_attempts(request):
    attempts = Attempt.objects.filter(user=request.user).order_by('-completed_at')
    return render(request, 'core/my_attempts.html', {'attempts': attempts})

