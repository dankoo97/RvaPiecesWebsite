import datetime

from django import forms
from django.core.validators import FileExtensionValidator

from events.models import LichessStudy, Event

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class LichessStudyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "lichess-study-form"
        self.helper.form_class = "lichess-study-form"
        self.helper.form_method = "post"

        self.helper.add_input(Submit("submit", "Add Study"))

    class Meta:
        model = LichessStudy
        fields = ["study_id", "tournament_date"]

        help_texts = {
            "study_id": "The study ID or study URL.",
            "tournament_date": "The date of the tournament.",
        }
        labels = {"study_id": "Study ID"}

        widgets = {
            "study_id": forms.TextInput(
                attrs={"placeholder": "https://lichess.org/study/abcdefgh"}
            ),
            "tournament_date": forms.DateInput(attrs={"type": "date"}),
        }


class LichessStudyGameSubmissionForm(forms.Form):
    event = forms.ModelChoiceField(
        queryset=Event.objects.all(), widget=forms.HiddenInput
    )
    study = forms.ModelChoiceField(
        queryset=LichessStudy.objects.all(), label="Lichess Study", empty_label=None
    )
    pgn_file = forms.FileField(
        label="PGN File",
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=["pgn"])],
    )
    pgn_text = forms.CharField(widget=forms.Textarea, required=False, label="PGN Text")

    _lifespan = 90

    def __init__(self, event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["event"].initial = event
        self.fields[
            "study"
        ].queryset = LichessStudyGameSubmissionForm.get_relevant_studies(event)

        self.helper = FormHelper()
        self.helper.form_id = "lichess-study-game-submission-form"
        self.helper.form_class = "lichess-study-game-submission-form"
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Submit Game"))

    @staticmethod
    def get_relevant_studies(event):
        earliest = datetime.datetime.today() - datetime.timedelta(
            days=LichessStudyGameSubmissionForm._lifespan
        )
        studies = event.lichess_studies.filter(
            tournament_date__gte=earliest,
            tournament_date__lte=datetime.datetime.today(),
        )
        return studies

    def clean(self):
        cleaned_data = super().clean()

        pgn_file = cleaned_data.get("pgn_file")
        pgn_text = cleaned_data.get("pgn_text")

        if not (pgn_file or pgn_text):
            raise forms.ValidationError(
                "You must provide either a PGN file or PGN text."
            )

        if pgn_file and pgn_text:
            raise forms.ValidationError(
                "You cannot provide both a PGN file and PGN text."
            )

        return cleaned_data
