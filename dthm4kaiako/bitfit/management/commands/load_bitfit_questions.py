"""Module for the custom Django loadbitfitquestions command."""

from django.core.management.base import BaseCommand
from django.conf import settings
from utils.LoaderFactory import LoaderFactory


class Command(BaseCommand):
    """Required command class for the custom Django loadbitfitquestions command."""

    help = 'Loads Bitfit questions into the database'

    def handle(self, *args, **options):
        """Automatically called when the loadbitfitquestions command is given."""
        base_path = settings.BITFIT_QUESTIONS_BASE_PATH
        questions_structure_file = 'questions.yaml'
        factory = LoaderFactory()

        factory.create_bitfit_questions_loader(
            structure_filename=questions_structure_file,
            base_path=base_path
        ).load()
