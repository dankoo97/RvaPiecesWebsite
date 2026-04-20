import datetime

from crispy_forms.bootstrap import FormActions, Modal, StrictButton
from django import forms
from django.templatetags.static import static

from events.models import LichessStudy

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, HTML, Div, Button, Field


class LichessStudyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "lichess-study-form"
        self.helper.form_class = "lichess-study-form"
        self.helper.form_method = "post"

        self.helper.add_input(Submit("_study", "Add Study"))

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
    study = forms.ModelChoiceField(
        queryset=LichessStudy.objects.all(), label="Lichess Study", empty_label=None
    )
    pgn = forms.CharField(widget=forms.HiddenInput, required=True, label="PGN Preview")

    # Board settings
    draggable_pieces = forms.BooleanField(
        label="Draggable Pieces",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    click_to_move = forms.BooleanField(
        label="Click to Move",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    move_table_view = forms.BooleanField(
        label="Move Table View",
        required=False,
    )

    text_manipulation_buttons = [
        {
            "id": "upload-pgn",
            "text": "Upload",
            "icon": "bi bi-upload",
            "title": "Upload PGN File",
        },
        {
            "id": "paste-pgn",
            "text": "Paste",
            "icon": "bi bi-clipboard-plus",
            "title": "Paste PGN",
        },
        {"id": "copy-pgn", "text": "Copy", "icon": "bi bi-copy", "title": "Copy PGN"},
        {"id": "clear-pgn", "text": "Clear", "icon": "bi bi-x", "title": "Clear PGN"},
    ]

    board_manipulation_buttons = [
        {"id": "to-start", "icon": "bi bi-skip-backward-fill", "title": "To Start"},
        {
            "id": "previous-move",
            "icon": "bi bi-arrow-left-circle-fill",
            "title": "Previous Move",
        },
        {
            "id": "next-move",
            "icon": "bi bi-arrow-right-circle-fill",
            "title": "Next Move",
        },
        {"id": "to-end", "icon": "bi bi-skip-forward-fill", "title": "To End"},
        {"id": "flip-board", "icon": "bi bi-arrow-down-up", "title": "Flip Board"},
        {
            "id": "undo-move",
            "icon": "bi bi-arrow-counterclockwise",
            "title": "Undo Move",
        },
    ]

    _lifespan = 90

    def __init__(self, event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[
            "study"
        ].queryset = LichessStudyGameSubmissionForm.get_relevant_studies(event)

        self.helper = FormHelper()
        self.helper.form_id = "lichess-study-game-submission-form"
        self.helper.form_class = "lichess-study-game-submission-form"
        self.helper.form_method = "post"

        board_wrapper = Div(
            Div(
                Div(
                    css_id="board",
                    css_class="game-board",
                    data_piece_url=static("images/chesspieces/wikipedia/"),
                    data_event_name=event.name,
                    data_event_location=event.location,
                ),
                Div(
                    Div(
                        *(
                            self.generate_button_layout(
                                self.board_manipulation_buttons[:4],
                                "btn-outline-dark btn-small board-manipulation-button",
                            )
                        ),
                        css_class="btn-group me-2 ms-md-3",
                        role="group",
                    ),
                    Div(
                        *(
                            self.generate_button_layout(
                                self.board_manipulation_buttons[4:],
                                "btn btn-outline-dark btn-small board-manipulation-button",
                            )
                        ),
                        css_class="btn-group me-2",
                        role="group",
                    ),
                    Div(
                        *(
                            self.generate_button_layout(
                                [
                                    {
                                        "id": "board-settings-button",
                                        "icon": "bi bi-gear-fill",
                                        "title": "Board Settings",
                                    }
                                ],
                                "btn btn-outline-dark btn-small board-manipulation-button",
                            )
                        ),
                        css_class="btn-group me-2",
                        role="group",
                    ),
                    css_class="btn-toolbar board-manipulation-buttons",
                    role="toolbar",
                ),
                css_id="board-wrapper",
                css_class="col-12 col-md-6 mb-3 mb-md-0",
            ),
            Div(
                Div(
                    css_id="move-list",
                    css_class="move-list mb-3 ms-md-3 rounded-4 bg-light",
                ),
                css_id="move-list-wrapper",
                css_class="col-12 col-md-6",
            ),
            css_class="row g-3 mb-3 align-items-start",
        )

        header_wrapper = Div(
            HTML("<label class='header-label' for='tag-container'>PGN Headers</label>"),
            Div(
                css_id="tag-container",
            ),
            Button(
                "add-header-btn",
                css_id="add-header-button",
                css_class="btn btn-small btn-outline-secondary mb-3",
                value="Add Header",
            ),
            css_id="header-root",
        )

        pgn_buttons_wrapper = FormActions(
            Div(
                Submit("submit", "Submit Game", css_class="btn-small me-2"),
                Div(
                    *(
                        self.generate_button_layout(
                            self.text_manipulation_buttons,
                            "btn btn-outline-dark btn-small text-manipulation-button",
                        )
                    ),
                    css_class="btn-group text-manipulation-buttons",
                    role="group",
                ),
                css_class="container btn-toolbar bg-light-subtle p-2 my-4 rounded",
                role="toolbar",
            )
        )

        board_settings_modal = Div(
            Modal(
                Div(
                    Div(
                        Div(
                            Div(
                                HTML(
                                    """
                                        <h2>Board Settings</h2>
                                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                    """
                                ),
                                css_class="modal-header",
                            ),
                            Div(
                                Field("draggable_pieces"),
                                Field("click_to_move"),
                                Field("move_table_view"),
                                css_class="modal-body",
                            ),
                        ),
                        css_class="modal-content",
                    ),
                    css_class="modal-dialog modal-dialog-centered modal-lg",
                ),
                css_id="board-settings-modal",
            )
        )

        self.helper.layout = Layout(
            Field("pgn"),
            Field("study"),
            board_wrapper,
            header_wrapper,
            pgn_buttons_wrapper,
            board_settings_modal,
        )

    @staticmethod
    def generate_button_layout(buttons, css_class=""):
        for i, button in enumerate(buttons):
            yield StrictButton(
                css_id=button["id"],
                css_class=css_class,
                title=button["title"],
                content=f"""
                    {"" if "text" not in button else "<span>" + button["text"] + "</span>"}
                    <i class="{button["icon"]}"></i>
                """,
            )

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
