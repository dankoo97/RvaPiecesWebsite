let chessnut_json = {events: []};
let deleted_chessnut_event_ids = [];

async function add_chessnut_event(chessnut_event_id, chessnut_event_name, expires) {
    // HTML
    const accordion = document.getElementById('chessnut-accordion')
    const accordion_item = document.createElement("div")

    accordion_item.classList.add("accordion-item")
    accordion_item.id = "chessnut-item-" + chessnut_event_id
    accordion_item.innerHTML = `
        <h2 class="accordion-header">
            <button class="accordion-button collapsed"
                    type="button"
                    data-bs-toggle="collapse"
                    data-bs-target="#chessnut-accordion-collapse-${chessnut_event_id}"
                    aria-expanded="false"
                    aria-controls="chessnut-accordion-collapse-${chessnut_event_id}">
                ${chessnut_event_name}
            </button>
        </h2>
        <div id="chessnut-accordion-collapse-${chessnut_event_id}"
             class="accordion-collapse collapse"
             aria-labelledby="heading-${chessnut_event_id}" data-bs-parent="#accordionChessnut">
            <div class="accordion-body">
                <div style="display:flex;flex-basis: auto; flex-direction: row;">
                    <div>
                        <p>Event details will be visible after submission</p>
                    </div>
                    <div class="ms-auto">
                        <button class="btn btn-danger" onclick="delete_chessnut_event(${chessnut_event_id})">Delete</button>
                    </div>
                </div>

            </div>
        </div>
    `
    // Adds the accordion item to the 3rd to last element of the accordion
    accordion.insertBefore(accordion_item, accordion.lastElementChild.previousElementSibling);

    // JSON
    chessnut_json["events"].push({
        id: chessnut_event_id,
        name: chessnut_event_name,
        expires: expires,
    })

    update_chessnut_event_select_list();
    enable_update_submission();
}

async function delete_chessnut_event(chessnut_event_id) {
    // HTML
    const chessnut_item_id = 'chessnut-item-' + chessnut_event_id;
    document.getElementById(chessnut_item_id).remove();

    // JSON
    const chessnut_event_index = chessnut_json["events"].findIndex(
        chessnut_event => String(chessnut_event.id) === String(chessnut_event_id)
    );
    if (chessnut_event_index !== -1) {
        chessnut_json["events"].splice(chessnut_event_index, 1);
    }
    if (!deleted_chessnut_event_ids.includes(String(chessnut_event_id))) {
        deleted_chessnut_event_ids.push(String(chessnut_event_id));
    }

    update_chessnut_event_select_list();
    enable_update_submission();
}

function enable_update_submission() {
    document.getElementById('submit-chessnut-updates').disabled = false;
}

function submit_chessnut_updates(event_slug) {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    fetch(`/events/event/${event_slug}/chessnut/`, {
        method: 'POST',
        headers: {
            "X-CSRFToken": csrftoken,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        },
        body: new URLSearchParams({
            "_update": `update chessnut_events`,
            "newJson": JSON.stringify(chessnut_json),
            "removedIds": JSON.stringify(deleted_chessnut_event_ids),
        })
    }).then(async response => {
        if (!response.ok) {
            const error = await response.text();
            throw new Error(error || `Update failed (${response.status})`);
        }
        window.location.reload();
    }).catch(error => window.alert(error.message));
}

function save_magic_chessnut_handler(event_slug) {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const days_before_start = document.getElementById('magic-handler-days-before').value;
    const days_after_end = document.getElementById('magic-handler-days-after').value;

    if (Number(days_before_start) < 0 || Number(days_after_end) < 0) {
        window.alert('The visibility windows cannot be negative.');
        return;
    }

    fetch(`/events/event/${event_slug}/chessnut/`, {
        method: 'POST',
        headers: {
            "X-CSRFToken": csrftoken,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        },
        body: new URLSearchParams({
            "_magic_update": "update magic chessnut handler",
            "enabled": document.getElementById('magic-handler-enabled').checked,
            "title_regex": document.getElementById('magic-handler-title-regex').value,
            "days_before_start": days_before_start,
            "days_after_end": days_after_end,
        })
    }).then(async response => {
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || `Save failed (${response.status})`);
        }
        window.location.reload();
    }).catch(error => window.alert(error.message));
}

function clear_magic_chessnut_ignored(event_slug) {
    if (!window.confirm('Allow previously ignored Chessnut events to be added again?')) {
        return;
    }

    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    fetch(`/events/event/${event_slug}/chessnut/`, {
        method: 'POST',
        headers: {
            "X-CSRFToken": csrftoken,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        },
        body: new URLSearchParams({
            "_magic_clear_ignored": "clear ignored chessnut events",
        })
    }).then(async response => {
        if (!response.ok) {
            throw new Error(`Clear ignored events failed (${response.status})`);
        }
        window.location.reload();
    }).catch(error => window.alert(error.message));
}

function get_chessnut_json_from_cookie() {
    const cookie = document.cookie
        .split('; ')
        .find(row => row.startsWith('chessnut_json='));

    if (!cookie) {
        return get_chessnut_json_from_dom();
    }

    const encoded_json = cookie.substring('chessnut_json='.length);
    const decoded_json = decodeURIComponent(encoded_json);
    const candidates = [
        decoded_json,
        decoded_json.replace(/\\054/g, ','),
        decoded_json.replace(/^"|"$/g, '').replace(/\\"/g, '"'),
    ];

    for (const candidate of candidates) {
        try {
            const parsed_json = JSON.parse(candidate);
            if (parsed_json && Array.isArray(parsed_json.events)) {
                parsed_json.events = parsed_json.events.map(event => ({
                    ...event,
                    id: String(event.id),
                }));
                return parsed_json;
            }
        } catch (error) {
            // Try the next cookie encoding format.
        }
    }

    console.error('Unable to read chessnut_json cookie:', encoded_json);
    return get_chessnut_json_from_dom();
}

function get_chessnut_json_from_dom() {
    return {
        events: Array.from(document.querySelectorAll('.accordion-item[data-chessnut-event-id]'))
            .map(event_element => ({
                id: String(event_element.dataset.chessnutEventId),
            })),
    };
}

function get_chessnut_json() {
    chessnut_json = get_chessnut_json_from_cookie() || {events: []};
}

function update_chessnut_event_select_list() {
    let chessnut_event_nodes = document.querySelectorAll('.accordion > .accordion-item');
    let chessnut_event_ids = [];
    for (let node of chessnut_event_nodes) {
        chessnut_event_ids.push(node.id.split('-')[2]);
    }
    const select_el = document.getElementById('id_chessnut_event')
    for (let node of select_el.childNodes) {
        if (node.value && chessnut_event_ids.includes(node.value)) {
            node.remove();
        }
    }
    update_searchable_chessnut_options();
}

let searchable_chessnut_input = null;
let searchable_chessnut_datalist = null;

function update_searchable_chessnut_options() {
    if (!searchable_chessnut_datalist) {
        return;
    }

    searchable_chessnut_datalist.replaceChildren();
    const select_el = document.getElementById('id_chessnut_event');
    for (const option of select_el.options) {
        const datalist_option = document.createElement('option');
        datalist_option.value = option.textContent;
        datalist_option.dataset.eventId = option.value;
        searchable_chessnut_datalist.appendChild(datalist_option);
    }
}

function setup_searchable_chessnut_select() {
    const select_el = document.getElementById('id_chessnut_event');
    if (!select_el || searchable_chessnut_input) {
        return;
    }

    searchable_chessnut_datalist = document.createElement('datalist');
    searchable_chessnut_datalist.id = 'chessnut-event-options';

    searchable_chessnut_input = document.createElement('input');
    searchable_chessnut_input.type = 'search';
    searchable_chessnut_input.className = 'form-control mb-2';
    searchable_chessnut_input.placeholder = 'Search Chessnut events';
    searchable_chessnut_input.setAttribute('list', searchable_chessnut_datalist.id);

    select_el.hidden = true;
    select_el.parentNode.insertBefore(searchable_chessnut_input, select_el);
    select_el.parentNode.insertBefore(searchable_chessnut_datalist, select_el);

    searchable_chessnut_input.addEventListener('input', () => {
        const matching_option = Array.from(select_el.options)
            .find(option => option.textContent === searchable_chessnut_input.value);
        select_el.value = matching_option ? matching_option.value : '';
    });

    update_searchable_chessnut_options();
}

document.getElementById('add-chessnut-event-button').addEventListener('show.bs.collapse', () => {
    setup_searchable_chessnut_select();
    update_chessnut_event_select_list();
});

document.getElementById('add-chessnut-event-button').addEventListener('shown.bs.collapse', () => {
    document.getElementById('button-id-chessnut').addEventListener('click', async () => {
        const select_el = document.getElementById('id_chessnut_event');
        const chessnut_event_id = select_el.value;
        const chessnut_event_name = select_el.options[select_el.selectedIndex].text;
        const expires = document.getElementById('id_expires').value;
        await add_chessnut_event(chessnut_event_id, chessnut_event_name, expires);
    });
});

document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(element => {
    new bootstrap.Tooltip(element);
});

get_chessnut_json();
