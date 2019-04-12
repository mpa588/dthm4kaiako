from django.shortcuts import render, redirect
from django.views import generic
from django.http import JsonResponse, Http404
from django.contrib import messages
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import serializers
import requests
import time
import datetime
import random
import json
from ast import literal_eval
import jinja2

from .forms import *
from bitfit.models import (
    Question,
    TestCase,
)


class IndexView(generic.base.TemplateView):
    """Homepage for BitFit."""

    template_name = 'bitfit/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = Question.objects.all()

        # if self.request.user.is_authenticated:
        #     user = User.objects.get(username=self.request.user.username)
        #     all_questions = Question.objects.all()
        #     attempted_questions = user.profile.attempted_questions.all()
        #     new_questions = all_questions.difference(attempted_questions)[:5]

        #     history = []
        #     for question in new_questions:
        #         if question.title not in [question['title'] for question in history]:
        #             history.append({'title': question.title, 'id': question.pk})
        #     context['history'] = history
        return context

class LastAccessMixin(object):
    def dispatch(self, request, *args, **kwargs):
        """update days logged in when user accesses a page with this mixin"""
        if request.user.is_authenticated:
            request.user.last_login = datetime.datetime.now()
            request.user.save(update_fields=['last_login'])

            profile = request.user.profile
            today = datetime.date.today()

            login_days = profile.loginday_set.order_by('-day')
            if len(login_days) > 1:
                request.user.last_login = login_days[1].day
                request.user.save(update_fields=['last_login'])

            if not login_days.filter(day=today).exists():
                day = LoginDay(profile=profile)
                day.full_clean()
                day.save()

        return super(LastAccessMixin, self).dispatch(request, *args, **kwargs)

def get_random_question(request, current_question_id):
    """redirect to random question user hasn't done, or to index page if there aren't any"""
    valid_question_ids = []
    if request.user.is_authenticated:
        user = User.objects.get(username=request.user.username)
        completed_questions = Question.objects.filter(profile=user.profile, attempt__passed_tests=True)
        valid_question_ids = [question.id for question in Question.objects.all() if question not in completed_questions]
    else:
        valid_question_ids = [question.id for question in Question.objects.all()]

    if current_question_id in valid_question_ids:
        valid_question_ids.remove(current_question_id)

    if len(valid_question_ids) < 1:
        url = '/'
    else:
        question_number = random.choice(valid_question_ids)
        url = '/questions/' + str(question_number)
    return redirect(url)


def add_points(question, profile, passed_tests):
    """add appropriate number of points (if any) to user's account"""
    max_points_from_attempts = 3
    points_for_correct = 10

    n_attempts = len(Attempt.objects.filter(question=question, profile=profile, is_save=False))
    previous_corrects = Attempt.objects.filter(question=question, profile=profile, passed_tests=True, is_save=False)
    is_first_correct = len(previous_corrects) == 1

    points_to_add = 0
    if n_attempts <= max_points_from_attempts:
        points_to_add += 1

    if passed_tests and is_first_correct:
        points_from_previous_attempts = n_attempts if n_attempts < max_points_from_attempts else max_points_from_attempts
        points_to_add += (points_for_correct - points_from_previous_attempts)

    profile.points += points_to_add
    profile.full_clean()
    profile.save()


def save_attempt(request):
    """save user's attempt and add points if necessary"""
    request_json = json.loads(request.body.decode('utf-8'))
    if request.user.is_authenticated:
        user = User.objects.get(username=request.user.username)
        profile = user.profile
        question = Question.objects.get(pk=request_json['question'])

        user_code = request_json['user_input']
        passed_tests = request_json['passed_tests']
        is_save = request_json['is_save']

        attempt = Attempt(profile=profile, question=question, user_code=user_code, passed_tests=passed_tests, is_save=is_save)
        attempt.full_clean()
        attempt.save()

        if not is_save:
            add_points(question, profile, passed_tests)

    result = {}
    return JsonResponse(result)


def save_goal_choice(request):
    """update user's goal choice in database"""
    request_json = json.loads(request.body.decode('utf-8'))
    if request.user.is_authenticated:
        user = User.objects.get(username=request.user.username)
        profile = user.profile

        goal_choice = request_json['goal_choice']
        profile.goal = int(goal_choice)
        profile.full_clean()
        profile.save()

    return JsonResponse({})


def get_consecutive_sections(days_logged_in):
    """return a list of lists of consecutive days logged in"""
    consecutive_sections = []

    today = days_logged_in[0]
    previous_section = [today]
    for day in days_logged_in[1:]:
        if day == previous_section[-1] - datetime.timedelta(days=1):
            previous_section.append(day)
        else:
            consecutive_sections.append(previous_section)
            previous_section = [day]

    consecutive_sections.append(previous_section)
    return consecutive_sections


def check_badge_conditions(user):
    """check badges for account creation, days logged in, and questions solved"""
    earned_badges = user.profile.earned_badges.all()

    # account creation badge
    try:
        creation_badge = Badge.objects.get(id_name="create-account")
        if creation_badge not in earned_badges:
            new_achievement = Earned(profile=user.profile, badge=creation_badge)
            new_achievement.full_clean()
            new_achievement.save()
    except (Badge.DoesNotExist):
        pass

    # consecutive days logged in badges
    login_badges = Badge.objects.filter(id_name__contains="login")
    for login_badge in login_badges:
        if login_badge not in earned_badges:
            n_days = int(login_badge.id_name.split("-")[1])

            days_logged_in = LoginDay.objects.filter(profile=user.profile)
            days_logged_in = sorted(days_logged_in, key=lambda k: k.day, reverse=True)
            sections = get_consecutive_sections([d.day for d in days_logged_in])

            max_consecutive = len(max(sections, key=lambda k: len(k)))

            if max_consecutive >= n_days:
                new_achievement = Earned(profile=user.profile, badge=login_badge)
                new_achievement.full_clean()
                new_achievement.save()

    # solved questions badges
    solve_badges = Badge.objects.filter(id_name__contains="solve")
    for solve_badge in solve_badges:
        if solve_badge not in earned_badges:
            n_problems = int(solve_badge.id_name.split("-")[1])
            n_completed = Attempt.objects.filter(profile=user.profile, passed_tests=True, is_save=False)
            n_distinct = n_completed.values("question__pk").distinct().count()
            if n_distinct >= n_problems:
                new_achievement = Earned(profile=user.profile, badge=solve_badge)
                new_achievement.full_clean()
                new_achievement.save()


def get_past_5_weeks(user):
    """get how many questions a user has done each week for the last 5 weeks"""
    t = datetime.date.today()
    today = datetime.datetime(t.year, t.month, t.day)
    last_monday = today - datetime.timedelta(days=today.weekday(), weeks=0)
    last_last_monday = today - datetime.timedelta(days=today.weekday(), weeks=1)

    past_5_weeks = []
    to_date = today
    for week in range(0, 5):
        from_date = today - datetime.timedelta(days=today.weekday(), weeks=week)
        attempts = Attempt.objects.filter(profile=user.profile, date__range=(from_date, to_date + datetime.timedelta(days=1)), is_save=False)
        distinct_questions_attempted = attempts.values("question__pk").distinct().count()

        label = str(week) + " weeks ago"
        if week == 0:
            label = "This week"
        elif week == 1:
            label = "Last week"

        past_5_weeks.append({'week': from_date, 'n_attempts': distinct_questions_attempted, 'label': label})
        to_date = from_date
    return past_5_weeks


class ProfileView(LoginRequiredMixin, generic.DetailView):
    """Displays a user's BitFit profile."""

    login_url = '/login/'
    redirect_field_name = 'next'
    template_name = 'bitfit/profile.html'
    model = User

    def get_object(self):
        if self.request.user.is_authenticated:
            return User.objects.get(username=self.request.user.username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # user = User.objects.get(username=self.request.user.username)
        # questions = user.profile.attempted_questions.all()

        # check_badge_conditions(user)

        # context['goal'] = user.profile.goal
        # context['all_badges'] = Badge.objects.all()
        # context['past_5_weeks'] = get_past_5_weeks(user)

        # history = []
        # for question in questions:
        #     if question.title not in [question['title'] for question in history]:
        #         attempts = Attempt.objects.filter(profile=user.profile, question=question, is_save=False)
        #         if len(attempts) > 0:
        #             max_date = max(attempt.date for attempt in attempts)
        #             completed = any(attempt.passed_tests for attempt in attempts)
        #             history.append({'latest_attempt': max_date,'title': question.title,'n_attempts': len(attempts), 'completed': completed, 'id': question.pk})
        # context['history'] = sorted(history, key=lambda k: k['latest_attempt'], reverse=True)
        return context



# class SkillView(LastAccessMixin, generic.DetailView):
#     """displays list of questions which involve this skill"""
#     template_name = 'bitfit/skill.html'
#     context_object_name = 'skill'
#     model = SkillArea

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)

#         skill = self.get_object()
#         questions = skill.questions.all()
#         context['questions'] = questions

#         if self.request.user.is_authenticated:
#             user = User.objects.get(username=self.request.user.username)

#             history = []
#             for question in questions:
#                 if question.title not in [question['title'] for question in history]:
#                     attempts = Attempt.objects.filter(profile=user.profile, question=question, is_save=False)
#                     attempted = False
#                     completed = False
#                     if len(attempts) > 0:
#                         attempted = True
#                         completed = any(attempt.passed_tests for attempt in attempts)
#                     history.append({'attempted': attempted, 'completed': completed,'title': question.title, 'id': question.pk})
#             context['questions'] = history
#         return context


class QuestionView(generic.base.TemplateView):
    """Displays a question for Bitfit.

    This view requires to retrieve the object first in the context,
    in order to determine the required template to render.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            self.question = Question.objects.get_subclass(
                pk=self.kwargs['pk']
            )
        except Question.DoesNotExist:
            raise Http404("No question matches the given ID.")
        context['question'] = self.question
        test_cases = self.question.test_cases.values()
        context['test_cases'] = test_cases
        context['test_cases_json'] = json.dumps(list(test_cases))

        # if self.request.user.is_authenticated:
        #     question = self.get_object()
        #     profile = self.request.user.profile
        #     all_attempts = Attempt.objects.filter(question=question, profile=profile)
        #     if len(all_attempts) > 0:
        #         context['previous_attempt'] = all_attempts.latest('date').user_code
        return context

    def get_template_names(self, **kwargs):
        """Returns  list of template name for rendering the template.

        Overrides default DetailView template method.
        """
        return ['bitfit/question_types/{}.html'.format(self.question.QUESTION_TYPE)]



# BASE_URL = "http://36adab90.compilers.sphere-engine.com/api/v3/submissions/"
# PYTHON = 116
# COMPLETED = 0

# def literal_eval_params(params_text):
#     """attempts to convert params to literal list"""
#     params = "[" + params_text + "]"
#     try:
#         test_params = literal_eval(params)
#         result = {
#             'params': test_params,
#             'error': ''
#         }
#     except:
#         message = "Input formatted incorrectly. Must be valid comma-separated python. Strings must be surrounded by quotes."
#         result = {
#             'params': '',
#             'error': message
#         }
#     return result

# def send_code(request):
#     """formats code using template then sends to SphereEngine"""
#     request_json = json.loads(request.body.decode('utf-8'))
#     question_id = request_json['question']
#     question = Question.objects.get_subclass(pk=question_id)

#     template_loader = jinja2.FileSystemLoader(searchpath="bitfit/wrapper_templates")
#     template_env = jinja2.Environment(loader=template_loader)
#     template_file = "common.py"
#     template = template_env.get_template(template_file)

#     is_func = isinstance(question, ProgrammingFunction) or isinstance(question, BuggyFunction)
#     is_buggy = isinstance(question, Buggy)

#     if is_buggy and not is_func:
#         user_input = ''
#     else:
#         user_input = request_json['user_input']

#     if is_func:
#         if is_buggy:
#             func_name = question.buggy.buggyfunction.function_name
#         else:
#             func_name = question.programming.programmingfunction.function_name
#     else:
#         func_name = ''

#     if is_buggy:
#         user_stdin = request_json['buggy_stdin']
#         inputs = [user_stdin.split('\n')]
#         expected_output = request_json['expected_print']
#         outputs = [expected_output]
#         if is_func:
#             eval_result = literal_eval_params(user_input)
#             if len(eval_result['error']) > 0:
#                 return JsonResponse(eval_result)
#             test_params = eval_result['params']

#             params = [test_params]
#             expected_return = request_json['expected_return']
#             returns = [literal_eval(expected_return) if expected_return != '' else None]
#         else:
#             params = [[]]
#             returns = []

#         user_input = question.buggy.buggy_program
#         n_test_cases = 1
#     else:
#         if is_func:
#             test_cases = question.programming.programmingfunction.testcasefunction_set.all()
#             params = [literal_eval_params(case.function_params)['params'] for case in test_cases]
#             returns = [literal_eval(case.expected_return) if case.expected_return != '' else None for case in test_cases]
#         else:
#             test_cases = question.programming.testcaseprogram_set.all()
#             params = [[]]
#             returns = []

#         inputs = [case.test_input.split('\n') for case in test_cases]
#         outputs = [literal_eval('"""' + case.expected_output + '"""') for case in test_cases]
#         n_test_cases = len(test_cases)

#     if not is_func:
#         user_input = user_input.replace('\n', '\n    ')

#     context_variables = {
#         'params': repr(params),
#         'inputs': repr(inputs),
#         'outputs': repr(outputs),
#         'returns': repr(returns),
#         'n_test_cases': n_test_cases,
#         'is_func': is_func,
#         'is_buggy': is_buggy,
#         'user_code': user_input.replace('\t', '    '),
#         'function_name': func_name
#     }
#     code = template.render(**context_variables)
#     #print(code)
#     token = "?access_token=" + Token.objects.get(pk='sphere').token

#     response = requests.post(BASE_URL + token, data = {"language": PYTHON, "sourceCode": code})
#     result = response.json()

#     return JsonResponse(result)

# def send_solution(request):
#     """formats correct solution for buggy question type then sends to SphereEngine"""
#     request_json = json.loads(request.body.decode('utf-8'))
#     question_id = request_json['question']
#     question = Question.objects.get_subclass(pk=question_id)
#     solution = question.solution

#     is_func = isinstance(question, ProgrammingFunction) or isinstance(question, BuggyFunction)
#     if is_func:
#         test_params = request_json['user_input']
#         func_name = question.buggy.buggyfunction.function_name
#     else:
#         test_params = ''
#         func_name = ''
#     test_input = request_json['buggy_stdin']

#     template_loader = jinja2.FileSystemLoader(searchpath="bitfit/wrapper_templates")
#     template_env = jinja2.Environment(loader=template_loader)
#     template_file = "common.py"
#     template = template_env.get_template(template_file)

#     eval_result = literal_eval_params(test_params)
#     if len(eval_result['error']) > 0:
#         return JsonResponse(eval_result)
#     test_params = eval_result['params']

#     params = [test_params]
#     inputs = [test_input.split('\n')]
#     outputs = ['']
#     returns = [None]

#     context_variables = {
#         'params': repr(params),
#         'inputs': repr(inputs),
#         'outputs': repr(outputs),
#         'returns': repr(returns),
#         'n_test_cases': 1,
#         'is_func': is_func,
#         'is_buggy': False,
#         'user_code': solution.replace('\t', '    ').replace('\n', '\n    '),
#         'function_name': func_name
#     }
#     code = template.render(**context_variables)
#     #print(code)
#     token = "?access_token=" + Token.objects.get(pk='sphere').token

#     response = requests.post(BASE_URL + token, data = {"language": PYTHON, "sourceCode": code})
#     result = response.json()

#     return JsonResponse(result)


# def get_output(request):
#     """gets code output from SphereEngine (stdout, stderr, and compiler error)"""
#     request_json = json.loads(request.body.decode('utf-8'))
#     submission_id = request_json['id']
#     question_id = request_json['question']

#     token = "?access_token=" + Token.objects.get(pk='sphere').token

#     params = {
#         "withOutput": True,
#         "withStderr": True,
#         "withCmpinfo": True
#     }
#     response = requests.get(BASE_URL + submission_id + token, params=params)
#     result = response.json()

#     if result["status"] == COMPLETED:
#         result["completed"] = True
#     else:
#         result["completed"] = False

#     return JsonResponse(result)
