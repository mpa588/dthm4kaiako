from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator

from model_utils.managers import InheritanceManager

SMALL = 100
LARGE = 500

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    points = models.IntegerField(default=0)
    goal = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(7)]
    )
    earned_badges = models.ManyToManyField('Badge', through='Earned')
    attempted_questions = models.ManyToManyField('Question', through='Attempt')

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance, points=0)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.full_clean()
    instance.profile.save()

class LoginDay(models.Model):
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE)
    day = models.DateField(auto_now_add=True)

    def __str__(self):
        return str(self.day)

class Badge(models.Model):
    id_name = models.CharField(max_length=SMALL, unique=True)
    display_name = models.CharField(max_length=SMALL)
    description = models.CharField(max_length=LARGE)

    def __str__(self):
        return self.display_name


class Earned(models.Model):
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE)
    badge = models.ForeignKey('Badge', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.date)

class Token(models.Model):
    name = models.CharField(max_length=SMALL, primary_key=True)
    token = models.CharField(max_length=LARGE)

    def __str__(self):
        return self.name


class Attempt(models.Model):
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE)
    question = models.ForeignKey('Question', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    user_code = models.TextField()
    passed_tests = models.BooleanField(default=False)
    is_save = models.BooleanField(default=False)
    skills_hinted = models.ManyToManyField('Skill', blank=True)

    def __str__(self):
        return "Attempted '" + str(self.question) + "' on " + str(self.date)


class Question(models.Model):
    title = models.CharField(max_length=SMALL)
    question_text = models.TextField()
    solution = models.TextField()
    skill_areas = models.ManyToManyField('SkillArea', related_name='questions')
    skills = models.ManyToManyField('Skill', blank=True)
    objects = InheritanceManager()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Parsons Problem"
        verbose_name_plural = "All Questions & Parsons Problems"


class Programming(Question):

    class Meta:
        verbose_name = "Programming Question (Program)"
        verbose_name_plural = "All Programming Questions"


class ProgrammingFunction(Programming):
    function_name = models.CharField(max_length=SMALL)

    class Meta:
        verbose_name = "Programming Question (Function)"
        verbose_name_plural = "All Function Programming Questions"

class Buggy(Question):
    buggy_program = models.TextField()

    class Meta:
        verbose_name = "Debugging Question (Program)"
        verbose_name_plural = "All Debugging Questions"

class BuggyFunction(Buggy):
    function_name = models.CharField(max_length=SMALL)

    class Meta:
        verbose_name = "Debugging Question (Function)"
        verbose_name_plural = "All Function Debugging Questions"

class TestCase(models.Model):
    test_input = models.CharField(max_length=LARGE, blank=True)
    expected_output = models.CharField(max_length=LARGE, blank=True)

    def __str__(self):
        return str(self.test_input) + ' -> ' + str(self.expected_output)

class TestCaseFunction(TestCase):
    function_params = models.CharField(max_length=LARGE, blank=True)
    expected_return = models.CharField(max_length=LARGE, blank=True, null=True)
    question = models.ForeignKey('ProgrammingFunction', on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Function Test Case"

class TestCaseProgram(TestCase):
    question = models.ForeignKey('Programming', on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Program Test Case"


class Skill(models.Model):
    name = models.CharField(max_length=SMALL)
    hint = models.CharField(max_length=LARGE)
    subskills = models.ManyToManyField('self', symmetrical=False, blank=True)

    def __str__(self):
        return self.name

class SkillArea(models.Model):
    name = models.CharField(max_length=SMALL)

    def __str__(self):
        return self.name
