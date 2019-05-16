"""Module for the custom Django sampledata command."""

import csv
import random
from django.core import management
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.utils.text import slugify
from allauth.account.models import EmailAddress
from resources.models import (
    Language,
    TechnologicalArea,
    ProgressOutcome,
    YearLevel,
    CurriculumLearningArea,
)
from events.models import (
    Location,
    Series,
)
from tests.resources.factories import (
    ResourceFactory,
    NZQAStandardFactory,
)
from tests.events.factories import (
    SponsorFactory,
    OrganiserFactory,
    EventFactory,
)
from tests.dtta.factories import (
    NewsArticleFactory,
    PageFactory,
    RelatedLinkFactory,
)
from bitfit.models import (
    QuestionTypeProgram,
    QuestionTypeProgramTestCase,
    QuestionTypeFunction,
    QuestionTypeFunctionTestCase,
    QuestionTypeParsons,
    QuestionTypeParsonsTestCase,
    Badge
)


LOG_HEADER = '\n{}\n' + ('-' * 20)


class Command(management.base.BaseCommand):
    """Required command class for the custom Django sampledata command."""

    help = "Add sample data to database."

    def handle(self, *args, **options):
        """Automatically called when the sampledata command is given."""
        if settings.DEPLOYMENT_TYPE == 'prod' and not settings.DEBUG:
            raise management.base.CommandError(
                'This command can only be executed in DEBUG mode on non-production website.'
            )

        # Clear all data
        print(LOG_HEADER.format('Wipe database'))
        management.call_command('flush', interactive=False)
        print('Database wiped.')

        print(LOG_HEADER.format('Create sample users'))
        User = get_user_model()
        # Create admin account
        admin = User.objects.create_superuser(
            'admin',
            'admin@dthm4kaiako.ac.nz',
            password=settings.SAMPLE_DATA_ADMIN_PASSWORD,
            first_name='Admin',
            last_name='Account'
        )
        EmailAddress.objects.create(
            user=admin,
            email=admin.email,
            primary=True,
            verified=True
        )
        print('Admin created.')

        # Create user account
        user = User.objects.create_user(
            'user',
            'user@dthm4kaiako.ac.nz',
            password=settings.SAMPLE_DATA_USER_PASSWORD,
            first_name='Alex',
            last_name='Doe'
        )
        EmailAddress.objects.create(
            user=user,
            email=user.email,
            primary=True,
            verified=True
        )
        print('User created.')

        # Resources
        print(LOG_HEADER.format('Resources sample data'))
        Language.objects.create(name='English', css_class='language-en')
        Language.objects.create(name='Māori', css_class='language-mi')
        print('Languages created.')

        curriculum_learning_areas = {
            'English': 'english',
            'Arts': 'arts',
            'Health and physical education': 'health-pe',
            'Learning languages': 'languages',
            'Mathematics and statistics': 'mathematics',
            'Science': 'science',
            'Social sciences': 'social-sciences',
            'Technology': 'technology',
        }
        for area_name, area_css_class in curriculum_learning_areas.items():
            CurriculumLearningArea.objects.create(
                name=area_name,
                css_class=area_css_class,
            )
        print('Curriculum learning areas created.')

        ta_ct = TechnologicalArea.objects.create(
            name='Computational thinking',
            abbreviation='CT',
            css_class='ta-ct',
        )
        for i in range(1, 9):
            ProgressOutcome.objects.create(
                name='Computational thinking - Progress outcome {}'.format(i),
                abbreviation='CT PO{}'.format(i),
                technological_area=ta_ct,
                css_class='po-ct',
            )
        ta_dddo = TechnologicalArea.objects.create(
            name='Designing and developing digital outcomes',
            abbreviation='DDDO',
            css_class='ta-dddo',
        )
        for i in range(1, 7):
            ProgressOutcome.objects.create(
                name='Designing and developing digital outcomes - Progress outcome {}'.format(i),
                abbreviation='DDDO PO{}'.format(i),
                technological_area=ta_dddo,
                css_class='po-dddo',
            )
        print('Technological areas created.')
        print('Progress outcomes created.')

        NZQAStandardFactory.create_batch(size=20)
        for i in range(0, 14):
            YearLevel.objects.create(
                level=i
            )
        print('NZQA standards created.')

        ResourceFactory.create_batch(size=20)
        print('Resources created.')

        # Events
        print(LOG_HEADER.format('Events sample data'))
        SponsorFactory.create_batch(size=10)
        print('Event sponsors created.')
        OrganiserFactory.create_batch(size=10)
        print('Event organisers created.')
        event_series = {
            (
                'Computer Science for High Schools',
                'CS4HS',
            ),
            (
                'Computer ScieBitFit nce for Primary Schools',
                'CS4PS',
            ),
            (
                'Computer Science for Professional Development',
                'CS4PD',
            ),
            (
                'Code Club for Teachers',
                'CC4T',
            ),
        }
        for (name, abbreviation) in event_series:
            Series.objects.create(
                name=name,
                abbreviation=abbreviation,
            )
        print('Event series created.')

        region_codes = dict()
        for (code, name) in Location.REGION_CHOICES:
            region_codes[name] = code
        with open('general/management/commands/sample-data/nz-schools.csv') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in random.sample(list(reader), 100):
                if row['Longitude'] and row['Latitude'] and row['Region']:
                    Location.objects.create(
                        name=row['Name'],
                        street_address=row['Street'],
                        suburb=row['Suburb'],
                        city=row['City'],
                        region=region_codes[row['Region']],
                        coords=Point(
                            float(row['Longitude']),
                            float(row['Latitude'])
                        ),
                    )
        print('Event locations created.')

        EventFactory.create_batch(size=50)
        print('Events created.')

        # DTTA
        print(LOG_HEADER.format('DTTA sample data'))
        NewsArticleFactory.create_batch(size=20)
        print('DTTA news articles created.')
        PageFactory.create_batch(size=5)
        print('DTTA pages created.')
        RelatedLinkFactory.create_batch(size=10)
        print('DTTA related links created.')

        # Bitfit
        print(LOG_HEADER.format('BitFit sample data'))
        question_1 = QuestionTypeProgram.objects.create(
            title='Say hello!',
            question_text='<p>Print the text <code>Hello world!</code></p>',
            solution='print("Hello world!")',
        )
        QuestionTypeProgramTestCase.objects.create(
            test_input='',
            expected_output='Hello world!',
            question=question_1,
        )

        question_2 = QuestionTypeProgram.objects.create(
            title='Add 10',
            question_text='<p>Write a program that asks for a number, adds 10 to the number, then prints it out.</p>',
            solution='number = int(input("Number:"))\nprint(number + 10)',
            slug=slugify('Add 10')
        )
        QuestionTypeProgramTestCase.objects.create(
            test_input='24\n25',
            expected_output='34',
            question=question_2,
        )
        QuestionTypeProgramTestCase.objects.create(
            test_input='36',
            expected_output='46',
            question=question_2,
        )

        question_3 = QuestionTypeFunction.objects.create(
            title='Doubler',
            question_text=(
                '<p>Write a function <code>doubler()</code> '
                'that takes a number and returns double the number.</p>'
            ),
            solution='def doubler(num):\n    return num * 2',
            slug=slugify('Doubler')
        )
        QuestionTypeFunctionTestCase.objects.create(
            test_code='print(doubler(2))',
            expected_output='4',
            question=question_3,
        )
        QuestionTypeFunctionTestCase.objects.create(
            test_code='print(doubler(3))',
            expected_output='6',
            question=question_3,
        )
        QuestionTypeFunctionTestCase.objects.create(
            test_code='print(doubler(15))',
            expected_output='30',
            question=question_3,
        )
        QuestionTypeFunctionTestCase.objects.create(
            test_code='print(doubler(99))',
            expected_output='198',
            question=question_3,
        )
        QuestionTypeFunctionTestCase.objects.create(
            test_code='print(doubler(-2))',
            expected_output='-4',
            question=question_3,
        )

        question_4 = QuestionTypeParsons.objects.create(
            title='Double evens',
            question_text=(
                '<p>Write a function <code>double_even(number)</code> '
                'that takes a number and returns double the number if it is even. Otherwise it returns the original number</p>'
            ),
            solution=(
                'def double_even(number):\n'
                '    if number % 2 == 0:\n'
                '        return number * 2\n'
                '    else:\n'
                '        return number'
            ),
            lines=(
                'def double_even(number):\n'
                'if number % 2 == 0:\n'
                'if number // 2 == 0:\n'
                'return number * 2\n'
                'return number x 2\n'
                'else:\n'
                'return number'
            ),
            slug=slugify('Double evens')
        )
        QuestionTypeParsonsTestCase.objects.create(
            test_code='print(double_even(2))',
            expected_output='4',
            question=question_4,
        )
        QuestionTypeParsonsTestCase.objects.create(
            test_code='print(double_even(8))',
            expected_output='16',
            question=question_4,
        )
        QuestionTypeParsonsTestCase.objects.create(
            test_code='print(double_even(3))',
            expected_output='3',
            question=question_4,
        )
        QuestionTypeParsonsTestCase.objects.create(
            test_code='print(double_even(11))',
            expected_output='11',
            question=question_4,
        )
        print('Programming question added.')

        Badge.objects.create(
            id_name='create-account',
            display_name='Created an account!',
            description='Created your very own account',
            icon_name='img/icons/bitfit/icons8-badge-create-account-48.png'
        )

        Badge.objects.create(
            id_name='questions-solved-1',
            display_name='Solved one question!',
            description='Solved your very first question',
            icon_name='img/icons/bitfit/icons8-question-solved-black-50.png'
        )

        Badge.objects.create(
            id_name='questions-solved-3',
            display_name='Solved three questions!',
            description='Solved three questions',
            icon_name='img/icons/bitfit/icons8-question-solved-bronze-50.png'
        )

        Badge.objects.create(
            id_name='attempts-made-1',
            display_name='Made your first attempt at a question!',
            description='Attempted one question',
            icon_name='img/icons/bitfit/icons8-attempt-made-black-50.png'
        )

        Badge.objects.create(
            id_name='attempts-made-10',
            display_name='Made 10 question attempts!',
            description='Attempted ten questions',
            icon_name='img/icons/bitfit/icons8-attempt-made-bronze-50.png'
        )

        Badge.objects.create(
            id_name='attempts-made-100',
            display_name='Made 100 question attempts!',
            description='Attempted one hundred questions',
            icon_name='img/icons/bitfit/icons8-attempt-made-silver-50.png'
        )

        Badge.objects.create(
            id_name='attempts-made-1000',
            display_name='Made 1000 question attempts!',
            description='Attempted one thousand questions',
            icon_name='img/icons/bitfit/icons8-attempt-made-gold-50.png'
        )
        print("Badges added.")
