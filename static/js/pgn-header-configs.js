const tagContainer = document.getElementById('tag-container');
let callback = () => {};

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

export function createHeader (key = "", value = "") {
    const row = document.createElement('div');
    row.setAttribute('class', 'input-group mb-3 tag-row');

    let tagList = document.getElementById('common-tags');
    if (!tagList) {
        tagList = document.createElement('datalist');
        tagList.setAttribute('id', 'common-tags');
        Object.keys(headerConfig).forEach(tag => {
            const option = document.createElement('option');
            option.value = tag;
            tagList.appendChild(option);
        })
        document.body.appendChild(tagList);
    }

    let keyInput = document.createElement('input');
    keyInput.className = 'form-control tag-key';
    keyInput.value = key;
    keyInput.setAttribute('list', 'common-tags');
    let valueInput = document.createElement('input');
    valueInput.className = 'form-control tag-value';

    let removeButton = document.createElement('button');
    removeButton.className = 'btn btn-outline-secondary remove-tag';
    removeButton.type = 'button';
    removeButton.innerHTML = '<i class="bi bi-trash"></i>';

    row.appendChild(keyInput);
    row.appendChild(valueInput);
    row.appendChild(removeButton);

    applyHeaderConfig(row, key);
    tagContainer.appendChild(row);

    return { row, keyInput, valueInput, removeButton };
}

export function updateHeaderRow(key, value) {
    let valueInput = tagContainer.querySelector(`input[name=${key.toLowerCase()}-value]`);
    if (!valueInput) {
        let { valueInput: v } = createHeader(key, value);
        valueInput = v;
    }

    switch (valueInput.type) {
        case 'date':
            valueInput.valueAsDate = new Date(value);
            break
        default:
            valueInput.value = value;
    }
}

export function updateHeadersFromPgn(headers) {
    for (const [key, value] of Object.entries(headers)) {
        if (!(value === '?' || value === '')) {
            updateHeaderRow(key, value);
        }
    }
}

export function setCallback(cb) {
    callback = cb;
}

tagContainer.addEventListener('input', event => {
    if (event.target.classList.contains('tag-key')) {
        const row = event.target.closest('.tag-row');
        applyHeaderConfig(row, event.target.value);
    }
    callback();
});

tagContainer.addEventListener('click', event => {
    if (event.target.classList.contains('remove-tag')) {
        const row = event.target.closest('.tag-row');
        row.remove();
    }
    callback();
});
