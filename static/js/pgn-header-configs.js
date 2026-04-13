export const headerConfig = {
    Event: {type: 'text', label: 'Event', placeholder: 'Event name'},
    Site: {type: 'text', label: 'Site', placeholder: 'Site'},
    Date: {type: 'date', label: 'Date', placeholder: 'Date',
        validate: (value) => new Date(value).toISOString().split('T')[0].replaceAll('-', '.')
    },
    Round: {type: 'number', label: 'Round', placeholder: 'Round'},
    White: {type: 'text', label: 'White', placeholder: 'White player'},
    Black: {type: 'text', label: 'Black', placeholder: 'Black player'},
    Result: {type: 'text', label: 'Result', placeholder: 'Result', suggestions: ['White wins', 'Black wins', 'Draw', '*'],
        validate: (value) => {
            switch (value.toLowerCase().replaceAll(' ', '')) {
                case 'whitewins':
                case '1-0':
                    return '1-0';
                case 'blackwins':
                case '0-1':
                    return '0-1';
                case 'draw':
                case '1/2-1/2':
                    return '1/2-1/2';
                default: return '*';
            }
        }},
    Annotator: {type: 'text', label: 'Annotator', placeholder: 'Annotator'},
    TimeControl: {type: 'text', label: 'Time control', placeholder: 'Time control'},
    Termination: {type: 'text', label: 'Termination', placeholder: 'Termination', suggestions: ['Checkmate', 'Stalemate', 'Draw by repetition', 'Fifty move rule', "Insufficient material", 'White resigns', 'Black resigns']},
    Board: {type: 'text', label: 'Board', placeholder: 'Board'},
    WhiteElo: {type: 'number', label: 'White Elo', placeholder: 'White Elo'},
    BlackElo: {type: 'number', label: 'Black Elo', placeholder: 'Black Elo'},
    ECO: {type: 'text', label: 'ECO', placeholder: 'ECO'},
}

// Typically required tags: https://en.wikipedia.org/wiki/Portable_Game_Notation#Seven_Tag_Roster
export const standardHeaders = [
    "Event",
    "Site",
    "Date",
    "Round",
    "White",
    "Black",
    "Result",
]

export function applyHeaderConfig (row, key) {
    const config = headerConfig[key] || {type: 'text', label: key, placeholder: ""};
    const keyInput = row.querySelector(".tag-key");
    const valueInput = row.querySelector(".tag-value");
    const datalistId = `datalist-${key.toLowerCase()}`;

    keyInput.setAttribute('name', key.toLowerCase() + '-key');
    valueInput.setAttribute('name', key.toLowerCase() + '-value');
    valueInput.type = config.type;
    valueInput.placeholder = config.placeholder;

    if (config.suggestions) {
        let datalist = document.getElementById(datalistId);
        if (!datalist) {
            datalist = document.createElement('datalist');
            datalist.setAttribute('id', datalistId);
            config.suggestions.forEach(suggestion => {
                const option = document.createElement('option');
                option.setAttribute('value', suggestion);
                datalist.appendChild(option);
            });
            document.body.appendChild(datalist);
        }
        valueInput.setAttribute('list', datalistId);
    }
}
