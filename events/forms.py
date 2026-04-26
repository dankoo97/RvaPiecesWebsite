import datetime

from crispy_forms.bootstrap import FormActions, Modal, StrictButton
from django import forms
from django.templatetags.static import static

from events.models import LichessStudy

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, HTML, Div, Button, Field, MultiField


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
    share_to_discord = forms.BooleanField(
        label="Share to Discord",
        required=False,
        initial=False,
        widget=forms.HiddenInput,
    )

    discord_white_player = forms.CharField(
        label="White player's discord",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "username"}),
    )

    discord_black_player = forms.CharField(
        label="Black player's discord",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "username"}),
    )

    discord_game_orientation = forms.ChoiceField(
        label="Game Orientation",
        required=False,
        choices=[
            ("white", "White"),
            ("black", "Black"),
        ],
        initial="white",
        widget=forms.Select(attrs={"class": "form-select"}),
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
                css_id="board",
                css_class="game-board",
                data_piece_url=static("images/chesspieces/wikipedia/"),
                data_event_name=event.name,
                data_event_location=event.location,
            ),
            css_id="board-wrapper",
            css_class="col-12 col-md-6 mb-3 mb-md-0",
        )

        move_list_wrapper = Div(
            Div(
                css_id="move-list",
                css_class="move-list mb-3 ms-md-3 rounded-4 bg-light move-list--inline",
            ),
            css_id="move-list-wrapper",
            css_class="col-12 col-md-6",
        )

        board_buttons = Div(
            Div(
                *(
                    self.generate_button_layout(
                        self.board_manipulation_buttons[:4],
                        "btn-outline-dark btn-small board-manipulation-button",
                    )
                ),
                css_class="btn-group me-2",
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
            css_class="btn-toolbar justify-content-center board-manipulation-buttons",
            role="toolbar",
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

        share_to_discord_accordion = Div(
            Div(
                HTML("""
                    <h2 class="accordion-header" id="share-to-discord-header">
                        <button type="button" data-bs-toggle="collapse" data-bs-target="#share-to-discord-collapse" aria-expanded="false" aria-controls="share-to-discord-collapse" class="accordion-button collapsed">
                            <i class="bi bi-x-lg me-2" id="share-to-discord-icon"></i>
                            Share to discord
                        </button>
                    </h2>
                """),
                Div(
                    Div(
                        MultiField(
                            "Discord Information",
                            # PrependedText("discord_white_player", "@"),
                            # PrependedText("discord_black_player", "@"),
                            "discord_game_orientation",
                        ),
                        css_class="accordion-body",
                    ),
                    css_id="share-to-discord-collapse",
                    css_class="accordion-collapse collapse",
                    data_bs_parent="#share-to-discord-accordion",
                ),
                css_class="accordion-item",
            ),
            css_class="accordion",
            css_id="share-to-discord-accordion",
        )

        # noinspection PyTypeChecker
        board_settings_modal = Div(
            Modal(
                Div(
                    Div(
                        Div(
                            Field(
                                "draggable_pieces",
                                role="switch",
                                css_class="form-check-input",
                                wrapper_class="form-check form-switch",
                            ),
                            Field(
                                "click_to_move",
                                role="switch",
                                css_class="form-check-input",
                                wrapper_class="form-check form-switch",
                            ),
                            Field(
                                "move_table_view",
                                role="switch",
                                css_class="form-check-input",
                                wrapper_class="form-check form-switch",
                            ),
                            css_class="modal-body",
                        ),
                        css_class="modal-content",
                    ),
                    css_class="modal-dialog modal-dialog-centered modal-lg",
                ),
                title="Board Settings",
                css_id="board-settings-modal",
            )
        )

        context_menu = Div(
            StrictButton(
                css_id="delete-from-here-button",
                css_class="btn btn-outline-danger btn-small",
                content="""
                    <i class="bi bi-trash"></i>
                    Delete From Here
                """,
                data_action="delete-from-here",
            ),
            css_id="move-list-menu",
            css_class="dropdown-menu move-list-menu",
        )

        self.helper.layout = Layout(
            Field("pgn"),
            Field("share_to_discord"),
            Field("study"),
            Div(
                Div(
                    board_wrapper,
                    board_buttons,
                    css_class="board-column col-12 col-md-6 d-flex flex-column",
                ),
                move_list_wrapper,
                css_class="row g-3 mb-3 align-items-start",
            ),
            header_wrapper,
            share_to_discord_accordion,
            pgn_buttons_wrapper,
            board_settings_modal,
            context_menu,
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
