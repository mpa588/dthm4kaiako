"""Factory for creating loader objects."""

from bitfit.management.commands._BitFitQuestionsLoader import BitFitQuestionsLoader


class LoaderFactory:
    """Factory for creating loader objects."""

    def create_bitfit_questions_loader(self, **kwargs):
        """Create Bitfit questions loader."""
        return BitFitQuestionsLoader(**kwargs)
