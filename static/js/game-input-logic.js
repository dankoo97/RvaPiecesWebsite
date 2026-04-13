import { Chess } from 'chess.js';
import { headerConfig, standardHeaders, applyHeaderConfig } from './pgn-header-configs';

let board = null;
let game = new Chess();
let plyCount = 0;
let isBoardAnimating = false;
const $pgn = $('#id_pgn');
const $board = $('#board');
const tagContainer = document.getElementById('tag-container');
const nextMoveButton = document.getElementById('next-move');
const previousMoveButton = document.getElementById('previous-move');
const moveList = document.getElementById('move-list');

// Game logic
function updateStatus (updateBoard = true) {
    // Headers
    let rowValues = tagContainer.querySelectorAll(".tag-row");
    for (const row of rowValues) {
        const key = row.querySelector(".tag-key").value;
        const value = row.querySelector(".tag-value").value;
        const config = headerConfig[key] || {type: 'text', label: key, placeholder: ""};
        if (!(key && value)) continue;
        game.setHeader(key, config.validate ? config.validate(value) : value);
    }

    // Update displayed board
    if (updateBoard) {
        // TODO: Animation is finicky, on rapid clicks it looks bad, lets disable animation on rapid clicks
        board.position(game.history({verbose:true})[plyCount]?.before || game.fen(), false)
        isBoardAnimating = true;
    }

    // Update board manip buttons
    nextMoveButton.disabled = plyCount === game.history().length;
    previousMoveButton.disabled = plyCount === 0;

    // Update hidden pgn value
    $pgn.val(game.pgn());
}

function generateFromPgn(pgn) {
    game.loadPgn(pgn);
    plyCount = game.history().length;
    updateHeadersFromPgn();
    clearMoveText();
    updateMoveText(...game.history({verbose:true}));
    updateStatus();
}

function updateMoveText (...newMoves) {
    let allMoves = Array.from(moveList.querySelectorAll('.move-text'));
    allMoves.forEach(el => el.classList.remove('current-position'));

    if (newMoves.length > 0) {
        for (const newMove of newMoves) {
            const el = createSinglePlyMoveText(newMove, allMoves.length + 1);
            allMoves.push(el);
        }
    }

    if (plyCount > 0) {
        const currentMove = allMoves[plyCount-1];
        currentMove.classList.add('current-position');
        currentMove.scrollIntoView({behavior: 'smooth', block: 'nearest', inline: 'nearest'});
    } else {
        moveList.scrollTop = 0;
    }
}

function createSinglePlyMoveText (newMove, moveNumber) {
    let newMoveEl = document.createElement('span');
    let moveText = newMove.san;
    let row = moveList.children[Math.floor((moveNumber-1)/2)];
    if (!row) {
        row = document.createElement('div');
        row.classList.add('row', 'align-items-center', 'move-row', 'mt-1');

        const moveNumberEl = document.createElement('span');
        moveNumberEl.classList.add('col-1', 'move-number', 'ms-3');
        moveNumberEl.innerHTML = `${Math.floor((moveNumber-1)/2) + 1}.`;
        row.appendChild(moveNumberEl);

        moveList.appendChild(row);
    }
    newMoveEl.innerHTML = moveText;
    newMoveEl.classList.add('col-3', 'move-text', 'ms-3');
    row.appendChild(newMoveEl);
    return newMoveEl;
}

function clearMoveText () {
    moveList.innerHTML = '';
}

function onDragStart (source, piece, position, orientation) {
    // Check if the game is over
    if (game.isGameOver()) return false;

    // Check if the piece is a valid piece for the current turn
    if ((plyCount % 2 === 0 && piece.search(/^b/) !== -1) || plyCount % 2 === 1 && piece.search(/^w/) !== -1) {
        return false;
    }
}

function onDrop (source, target) {
    let move = null;
    try {
        // Prevent creating moves when the board does not appear at the most recent position
        const history = game.history({verbose:true});
        if (plyCount === history.length){
            move = game.move({
                from: source,
                to: target,
                promotion: 'q'
            });
        // Recreating historical move
        } else if (history[plyCount]?.from === source && history[plyCount]?.to === target){
            plyCount++;
            updateStatus();
            updateMoveText();
            return;
        } else {
            return 'snapback';
        }

    } catch (e) {
        if (e.message.includes('Invalid move')) {
            return 'snapback';
        } else {
            throw e;
        }
    }

    if (game.isGameOver()) {
        if (game.isDraw()) {
            updateHeader('Result', '1/2-1/2');
            if (game.isStalemate()) {
                updateHeader('Termination', 'Stalemate');
            } else if (game.isThreefoldRepetition()) {
                updateHeader('Termination', 'Threefold repetition');
            } else if (game.isDrawByFiftyMoves()) {
                updateHeader('Termination', 'Draw by fifty moves');
            } else if (game.isInsufficientMaterial()) {
                updateHeader('Termination', 'Insufficient material');
            }
        } else if (game.turn() === 'b') {
            updateHeader('Result', '1-0');
        } else if (game.turn() === 'w') {
            updateHeader('Result', '0-1');
        }
    }

    plyCount++;
    updateStatus();
    updateMoveText(move);
}

function onSnapEnd () {
    updateStatus(false);
}

function createHeader (key = "", value = "") {
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

    row.querySelector('.remove-tag').addEventListener('click', () => {
        row.remove();
        updateStatus();
    });

    applyHeaderConfig(row, key);
    tagContainer.appendChild(row);

    return { row, keyInput, valueInput, removeButton };
}

function createCommonHeaders () {
    standardHeaders.forEach(h => {
        createHeader(h);
    });

    // We can generate some defaults based on event info
    let event_name = $board.data('event-name');
    let event_location = $board.data('event-location');
    updateHeader('Event', event_name);
    updateHeader('Site', event_location);
    updateHeader('Date', Date.now());
}

function updateHeader (key, value) {
    if (!value) {
        game.removeHeader(key);
        return;
    }

    game.setHeader(key, value);
    updateHeaderRow(key, value);
}

function updateHeaderRow(key, value) {
    let valueInput = tagContainer.querySelector(`input[name=${key.toLowerCase()}-value]`);
    if (!valueInput) {
        let { valueInput: v } = createHeader(key, value);
        valueInput = v;
    }

    if (key.includes('Date') && valueInput.type === 'date') {
        valueInput.valueAsDate = new Date(value);
    } else {
        valueInput.value = value;
    }
}

function updateHeadersFromPgn() {
    let headers = game.getHeaders();
    for (const [key, value] of Object.entries(headers)) {
        if (!(value === '?' || value === '')) {
            updateHeaderRow(key, value);
        }
    }
}

function resizeBoard () {
    const boardElement = document.getElementById('board');
    if (!boardElement) return;

    const size = Math.min(window.innerWidth - 16, 600);
    boardElement.style.width = `${size}px`;
    boardElement.style.height = `${size}px`;
    board.resize();
}

window.addEventListener('resize', resizeBoard);
window.addEventListener('orientationchange', resizeBoard);

document.getElementById('add-header-button').onclick = () => createHeader();


// Board manipulation buttons
document.getElementById('to-start').onclick = () => {
    plyCount = 0;
    updateStatus();
    updateMoveText();
}

document.getElementById('to-end').onclick = () => {
    plyCount = game.history().length;
    updateStatus();
    updateMoveText();
}

nextMoveButton.onclick = () => {
    plyCount++;
    updateStatus();
    updateMoveText();
}

previousMoveButton.onclick = () => {
    plyCount--;
    updateStatus();
    updateMoveText();
}

document.getElementById('flip-board').onclick = () => {
    board.flip();
}

moveList.addEventListener('click', (event) => {
    const move = event.target;
    if (move.classList.contains('move-text')) {
        plyCount = Array.from(moveList.querySelectorAll('.move-text')).indexOf(move) + 1;
        updateMoveText();
        updateStatus();
    }
})

// Pgn manipulation buttons
document.getElementById('upload-pgn').onclick = () => {
    let fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.pgn';
    fileInput.addEventListener('input', () => {
        const file = fileInput.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                // TODO: Chessjs doesn't seem to like engine comments, so we remove them for now
                let withoutComments = e.target.result.replace(/(\{[^}]*\})+/g, '');
                generateFromPgn(withoutComments);
            } catch (e) {
                console.error('Error parsing PGN:', e);
                alert('Error parsing PGN. Please check the console for more details.');
            }
        };
        reader.readAsText(file);
    });

    fileInput.click();
};

document.getElementById('paste-pgn').onclick = async () => {
    try {
        let text = await navigator.clipboard.readText()
        generateFromPgn(text);
    } catch (err) {
        console.error('Failed to read clipboard contents:', err);
    }
}

document.getElementById('copy-pgn').onclick = async () => {
    await navigator.clipboard.writeText(game.pgn());
}

document.getElementById('clear-pgn').onclick = () => {
    game.reset();
    board.position(game.fen());
    tagContainer.querySelectorAll('.tag-row').forEach(row => {row.remove()});
    clearMoveText();
    createCommonHeaders();
    updateStatus();
    updateMoveText();
}

tagContainer.addEventListener('input', event => {
    if (event.target.classList.contains('tag-key')) {
        const row = event.target.closest('.tag-row');
        applyHeaderConfig(row, event.target.value);
    }
    updateStatus();
})

// Prevent form submission on Enter key press
document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector('form');
    if (!form) return;
    form.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
        }
    });
});

document.addEventListener('keydown', (event) => {
    switch (event.key) {
        case "ArrowRight":
            nextMoveButton.click();
            event.preventDefault();
            break;
        case "ArrowLeft":
            previousMoveButton.click();
            event.preventDefault();
            break;
        case "ArrowUp":
            document.getElementById('to-start').click();
            event.preventDefault();
            break;
        case "ArrowDown":
            document.getElementById('to-end').click();
            event.preventDefault();
            break;
    }
});

document.getElementById('board').onclick = (event) => {
    const square = event.target.dataset.square;
};


let pieceBaseUrl = $board.data('piece-url')
let config = {
    draggable: true,
    position: 'start',
    onDragStart: onDragStart,
    onDrop: onDrop,
    onSnapEnd: onSnapEnd,
    pieceTheme: pieceBaseUrl + '{piece}.png',

    // Animation callbacks?
    // onMoveEnd: () => {
    //     isBoardAnimating = false;
    // },
    // onChange: () => {
    //     isBoardAnimating = false;
    // },
};

board = Chessboard('board', config);
game = new Chess();
createCommonHeaders();
resizeBoard();
updateStatus();
