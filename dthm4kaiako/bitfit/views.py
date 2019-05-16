from django.shortcuts import render, redirect
from django.views import generic
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib import messages
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core import serializers
import requests
import time
import datetime
import random
import json
from ast import literal_eval
import jinja2
import logging

from bitfit.models import (
    Profile,
    Question,
    TestCase,
    Attempt,
    Badge, Earned, LoginDay)

logger = logging.getLogger(__name__)
del logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'incremental': True,
    'root': {
        'level': 'DEBUG',
    },
}

class IndexView(generic.base.TemplateView):
    """Homepage for BitFit."""

    template_name = 'bitfit/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = Question.objects.select_subclasses()

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

# class LastAccessMixin(object):
#     def dispatch(self, request, *args, **kwargs):
#         """update days logged in when user accesses a page with this mixin"""
#         if request.user.is_authenticated:
#             request.user.last_login = datetime.datetime.now()
#             request.user.save(update_fields=['last_login'])

#             profile = request.user.profile
#             today = datetime.date.today()

#             login_days = profile.loginday_set.order_by('-day')
#             if len(login_days) > 1:
#                 request.user.last_login = login_days[1].day
#                 request.user.save(update_fields=['last_login'])

#             if not login_days.filter(day=today).exists():
#                 day = LoginDay(profile=profile)
#                 day.full_clean()
#                 day.save()

#         return super(LastAccessMixin, self).dispatch(request, *args, **kwargs)

# def get_random_question(request, current_question_id):
#     """redirect to random question user hasn't done, or to index page if there aren't any"""
#     valid_question_ids = []
#     if request.user.is_authenticated:
#         user = User.objects.get(username=request.user.username)
#         completed_questions = Question.objects.filter(profile=user.profile, attempt__passed_tests=True)
#         valid_question_ids = [question.id for question in Question.objects.all() if question not in completed_questions]
#     else:
#         valid_question_ids = [question.id for question in Question.objects.all()]

#     if current_question_id in valid_question_ids:
#         valid_question_ids.remove(current_question_id)

#     if len(valid_question_ids) < 1:
#         url = '/'
#     else:
#         question_number = random.choice(valid_question_ids)
#         url = '/questions/' + str(question_number)
#     return redirect(url)


def add_points(question, profile, attempt):
    """add appropriate number of points (if any) to user's account"""
    max_points_from_attempts = 3
    points_for_correct = 10

    n_attempts = len(Attempt.objects.filter(question=question, profile=profile, is_save=False))
    previous_corrects = Attempt.objects.filter(question=question, profile=profile, passed_tests=True, is_save=False)
    is_first_correct = len(previous_corrects) == 1

    points_to_add = 0
    if n_attempts <= max_points_from_attempts:
        points_to_add += 1

    if attempt.passed_tests and is_first_correct:
        points_from_previous_attempts = n_attempts if n_attempts < max_points_from_attempts else max_points_from_attempts
        points_to_add += (points_for_correct - points_from_previous_attempts)

    profile.points += points_to_add
    profile.full_clean()
    profile.save()


def save_question_attempt(request):
    """Save user's attempt for a question.

    If the attempt is successful: add points if these haven't already
    been added.

    Args:
        request (Request): AJAX request from user.

    Returns:
        JSON response with result.
    """
    result = {
        'success': False,
    }
    if request.is_ajax():
        if request.user.is_authenticated:
            request_json = json.loads(request.body.decode('utf-8'))
            profile = request.user.profile
            question = Question.objects.get(pk=request_json['question'])
            user_code = request_json['user_input']
            passed_tests = request_json['passed_tests']
            # is_save = request_json['is_save']

            attempt = Attempt.objects.create(
                profile=profile,
                question=question,
                user_code=user_code,
                passed_tests=passed_tests,
            )
            result['success'] = True

            add_points(question, profile, attempt)

    return JsonResponse(result)

def save_goal_choice(request):
    """update user's goal choice in database"""
    request_json = json.loads(request.body.decode('utf-8'))
    if request.user.is_authenticated:
        user = request.user
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
    except Badge.DoesNotExist:
        logger.warning("No such badge: create-account")
        pass

    try:
        question_badges = Badge.objects.filter(id_name__contains="questions-solved")
        solved = Attempt.objects.filter(profile=user.profile, passed_tests=True)
        for question_badge in question_badges:
            if question_badge not in earned_badges:
                num_questions = int(question_badge.id_name.split("-")[2])
                if len(solved) >= num_questions:
                    new_achievement = Earned(profile=user.profile, badge=question_badge)
                    new_achievement.full_clean()
                    new_achievement.save()
    except Badge.DoesNotExist:
        logger.warning("No such badges: questions-solved")
        pass

    try:
        attempt_badges = Badge.objects.filter(id_name__contains="attempts-made")
        attempted = Attempt.objects.filter(profile=user.profile)
        for attempt_badge in attempt_badges:
            if attempt_badge not in earned_badges:
                num_questions = int(attempt_badge.id_name.split("-")[2])
                logger.warning(attempt_badge.id_name)
                logger.warning(num_questions)
                logger.warning(len(attempted))
                if len(attempted) >= num_questions:
                    logger.warning("making badge")
                    new_achievement = Earned(profile=user.profile, badge=attempt_badge)
                    new_achievement.full_clean()
                    new_achievement.save()
    except Badge.DoesNotExist:
        logger.warning("No such badges: questions-solved")
        pass


    # consecutive days logged in badges
    # login_badges = Badge.objects.filter(id_name__contains="login")
    # for login_badge in login_badges:
    #     if login_badge not in earned_badges:
    #         n_days = int(login_badge.id_name.split("-")[1])
    #
    #         days_logged_in = LoginDay.objects.filter(profile=user.profile)
    #         days_logged_in = sorted(days_logged_in, key=lambda k: k.day, reverse=True)
    #         sections = get_consecutive_sections([d.day for d in days_logged_in])
    #
    #         max_consecutive = len(max(sections, key=lambda k: len(k)))
    #
    #         if max_consecutive >= n_days:
    #             new_achievement = Earned(profile=user.profile, badge=login_badge)
    #             new_achievement.full_clean()
    #             new_achievement.save()


def get_past_5_weeks(user):
    """get how many questions a user has done each week for the last 5 weeks"""
    t = datetime.date.today()
    today = datetime.datetime(t.year, t.month, t.day)
    last_monday = today - datetime.timedelta(days=today.weekday(), weeks=0)
    last_last_monday = today - datetime.timedelta(days=today.weekday(), weeks=1)

    past_5_weeks = []
    to_date = today
    # for week in range(0, 5):
    #     from_date = today - datetime.timedelta(days=today.weekday(), weeks=week)
    #     attempts = Attempt.objects.filter(profile=user.profile, date__range=(from_date, to_date + datetime.timedelta(days=1)), is_save=False)
    #     distinct_questions_attempted = attempts.values("question__pk").distinct().count()-
    #
    #     label = str(week) + " weeks ago"
    #     if week == 0:
    #         label = "This week"
    #     elif week == 1:
    #         label = "Last week"
    #
    #     past_5_weeks.append({'week': from_date, 'n_attempts': distinct_questions_attempted, 'label': label})
    #     to_date = from_date
    return past_5_weeks


class ProfileView(LoginRequiredMixin, generic.DetailView):
    """Displays a user's BitFit profile."""

    login_url = '/login/'
    redirect_field_name = 'next'
    template_name = 'bitfit/profile.html'
    model = Profile

    def get_object(self):
        if self.request.user.is_authenticated:
            return Profile.objects.get(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        # questions = user.profile.attempted_questions.all()

        check_badge_conditions(user)

        context['goal'] = user.profile.goal
        logger.warning(user.profile.goal)
        context['all_badges'] = Badge.objects.all()
        context['past_5_weeks'] = get_past_5_weeks(user)

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

        if self.request.user.is_authenticated:
            try:
                previous_attempt = Attempt.objects.filter(
                    profile=self.request.user.profile,
                    question=self.question,
                ).latest('datetime')
            except ObjectDoesNotExist:
                previous_attempt = None
            context['previous_attempt'] = previous_attempt
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

