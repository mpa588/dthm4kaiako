"""Custom loader for loading Bitfit questions."""

from os.path import join
from django.db import transaction
from utils.TranslatableModelLoader import TranslatableModelLoader
from utils.errors import (
    MissingRequiredFieldError,
    InvalidYAMLValueError,
    CouldNotFindMarkdownFileError,
)
from utils.language_utils import get_available_languages
from bitfit.models import (
    QuestionTypeProgram,
    QuestionTypeFunction,
    QuestionTypeParsons,
)

VALID_QUESTION_TYPES = {
    QuestionTypeProgram.QUESTION_TYPE: QuestionTypeProgram,
    QuestionTypeFunction.QUESTION_TYPE: QuestionTypeFunction,
    QuestionTypeParsons.QUESTION_TYPE: QuestionTypeParsons,
}
VALID_QUESTION_TYPE_SETS = [
    {QuestionTypeFunction.QUESTION_TYPE, QuestionTypeParsons.QUESTION_TYPE},
]


class BitFitQuestionsLoader(TranslatableModelLoader):
    """Custom loader for loading Bitfit questions."""

    @transaction.atomic
    def load(self):
        """Load the content for Bitfit questions.

        Raise:
            MissingRequiredFieldError: when no object can be found with the matching
                attribute.
        """
        questions_structure = self.load_yaml_file(self.structure_file_path)

        for (question_slug, question_data) in questions_structure.items():
            if 'type' in question_data:
                question_types = [question_data['type']]
            elif 'types' in question_data:
                question_types = question_data['type']
            else:
                raise MissingRequiredFieldError(
                    self.structure_file_path,
                    [
                        'types/types',
                    ],
                    'Bitfit Question'
                )

            # Check question types are valid
            for question_type in question_types:
                if question_type not in VALID_QUESTION_TYPES.keys():
                    raise InvalidYAMLValueError(
                        self.structure_file_path,
                        'type',
                        'One of {}'.format(VALID_QUESTION_TYPES.keys())
                    )
                if len(question_types) > 1:
                    if set(question_types) not in VALID_QUESTION_TYPE_SETS:
                        raise InvalidYAMLValueError(
                            self.structure_file_path,
                            'types',
                            'Invalid pairing of types, must be one of {}'.format(VALID_QUESTION_TYPE_SETS)
                        )

            question_translations = self.get_blank_translation_dictionary()

            content_filename = join(question_slug, 'question.md')
            content_translations = self.get_markdown_translations(content_filename)
            for language, content in content_translations.items():
                question_translations[language]['title'] = content.title
                question_translations[language]['question_text'] = content.html_string

            solution_filename = join(question_slug, 'solution.py')
            for language in get_available_languages():
                solution = open(self.get_localised_file(language, solution_filename), encoding='UTF-8').read()
                question_translations[language]['solution'] = solution

            for question_type in question_types:
                question_class = VALID_QUESTION_TYPES[question_type]
                question, created = question_class.objects.get_or_create(
                    slug=question_slug,
                    defaults={
                        # Example line
                        # 'points': question_data['points'],
                    },
                )

                self.populate_translations(question, question_translations)
                self.mark_translation_availability(question, required_fields=['title', 'question_text'])
                question.save()

                if created:
                    self.log("Added Bitfit Question: {}".format(question.title))
                else:
                    self.log("Updated Bitfit Question: {}".format(question.title))
        self.log("All Bitfit questions loaded!\n")
