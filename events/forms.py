import datetime

from crispy_forms.bootstrap import FormActions, Modal, StrictButton
from django import forms
from django.templatetags.static import static

from events.chessnut import Chessnut
from events.models import LichessStudy

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, HTML, Div, Button, Field, MultiField


class LichessStudyForm(forms.ModelForm):
    chessnut_event_id = forms.ChoiceField(
        label="Chessnut Event",
        choices=(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, event=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if event is not None:
            chessnut_events = (event.chessnut_events or {}).get("events", [])
            self.fields["chessnut_event_id"].choices = [
                ("", "Select a Chessnut event")
            ] + [
                (str(chessnut_event["id"]), chessnut_event["name"])
                for chessnut_event in chessnut_events
            ]

        self.fields["study_id"].required = False

        self.lichess_studies = LichessStudy.get_all_lichess_studies()

        study_datalist_id = "study-name-datalist"
        options_html = "".join(
            [
                f'<option value="{study["name"]}" data-study_id="{study["id"]}">'
                for study in self.lichess_studies
            ]
        )
        options_js = f"""
            const datalist = document.getElementById("{study_datalist_id}");
            const studyMap = new Map();
            datalist.childNodes.forEach(option => {{
                studyMap.set(option.value, option.dataset.study_id);
            }});

            document.getElementById("id_name").addEventListener("input", (e) => {{
                const value = e.target.value;
                if (studyMap.has(value)) {{
                    document.getElementById("id_study_id").value = studyMap.get(value);
                }} else {{
                    document.getElementById("id_study_id").value = "";
                }}
            }});
        """

        self.helper = FormHelper()
        self.helper.form_id = "lichess-study-form"
        self.helper.form_class = "lichess-study-form"
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Div(
                Div(
                    Field("name", placeholder="Search or create a study"),
                    Field("study_id", type="hidden"),
                    Field("tournament_date"),
                    Field("chessnut_event_id"),
                    HTML(
                        f"<datalist id='study-name-datalist'>{options_html}</datalist>"
                    ),
                    HTML(
                        f'<script type="application/javascript">{options_js}</script>'
                    ),
                    css_class="col-12 col-md-6",
                ),
            )
        )

        self.helper.add_input(Submit("_study", "Add Study"))

    class Meta:
        model = LichessStudy
        fields = ["study_id", "name", "tournament_date", "chessnut_event_id"]

        help_texts = {
            "name": "Lichess study",
            "tournament_date": "The date of the tournament",
        }
        labels = {
            "name": "Lichess Study",
            "chessnut_event_id": "Chessnut Event",
        }

        widgets = {
            "name": forms.TextInput(
                attrs={"list": "study-name-datalist", "autocomplete": "off"}
            ),
            "tournament_date": forms.DateInput(attrs={"type": "date"}),
        }


class LichessStudyGameSubmissionForm(forms.Form):
    study = forms.ModelChoiceField(
        queryset=LichessStudy.objects.all(), label="Lichess Study", empty_label=None
    )
    chessnut_event_id = forms.CharField(widget=forms.HiddenInput, required=False)
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

    def __init__(self, event, chessnut_event_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["study"].queryset = event.lichess_studies.all()

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
            Field("chessnut_event_id"),
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
            # Hidden
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


class ChessnutForm(forms.Form):
    chessnut_event = forms.ChoiceField()
    expires = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "chessnut-event-form"
        self.helper.form_class = "chessnut-event-form"
        self.helper.form_method = "post"

        self.fields["chessnut_event"].choices = self.get_chessnut_events()

        self.helper.layout = Layout(
            Div(
                Field("chessnut_event"),
                Field("expires"),
            )
        )

        self.helper.add_input(Button("_chessnut", "Connect Chessnut Event"))

    @staticmethod
    def get_chessnut_events():
        result = Chessnut().get_all_chessnut_events()
        return [(e["id"], e["name"]) for e in result]
