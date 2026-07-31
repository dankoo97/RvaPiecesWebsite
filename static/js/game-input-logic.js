import { Chess } from 'chess.js';
import {
    headerConfig,
    standardHeaders,
    createHeader,
    updateHeaderRow,
    updateHeadersFromPgn,
    setCallback as setHeaderCallback,
} from './pgn-header-configs';
import {
    clearMoveList,
    getPly,
    nextMove,
    prevMove,
    setPly,
    toEnd,
    toStart,
    updateMoveText,
    setCallback as setMoveTextCallback,
    setClickMoveFromListFn,
    undoLastMove, setDeleteMoveFromListFn, setCurrentPositionCls,
} from './pgn-move-text';
import { onDragStart, onDrop, onSnapEnd, setConfig as setBoardEventConfig } from './board-events';

let board = null;
let game = new Chess();
const $pgn = $('#id_pgn');
const $board = $('#board');
const tagContainer = document.getElementById('tag-container');
const nextMoveButton = document.getElementById('next-move');
const previousMoveButton = document.getElementById('previous-move');

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
        board.position(game.history({verbose:true})[getPly()]?.before || game.fen(), false)
    }

    // Update board manip buttons
    nextMoveButton.disabled = getPly() === game.history().length;
    previousMoveButton.disabled = getPly() === 0;

    setCurrentPositionCls();
    // Update hidden pgn value
    $pgn.val(game.pgn());
}

function undoMove () {
    if (getPly() === 0) return;
    game.undo();
    undoLastMove();
    updateStatus();
}

function generateFromPgn(pgn) {
    try {
        game.loadPgn(pgn);
    } catch (e) {
        // Try without comments...
        game.loadPgn(pgn.replace(/(\{[^}]*\})+/g, ''));
    }
    clearMoveList();
    updateHeadersFromPgn(game.getHeaders());
    updateMoveText(...game.history({verbose:true}));
    setPly(game.history().length);
    updateStatus();
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
    const easternDateParts = new Intl.DateTimeFormat('en-US', {
        timeZone: 'America/New_York',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
    }).formatToParts(new Date(Date.now()));
    const easternDate = Object.fromEntries(
        easternDateParts
            .filter(part => ['year', 'month', 'day'].includes(part.type))
            .map(part => [part.type, part.value])
    );
    updateHeader('Date', `${easternDate.year}.${easternDate.month}.${easternDate.day}`);
}

function updateHeader (key, value) {
    if (!value) {
        game.removeHeader(key);
        return;
    }
    game.setHeader(key, value);
    updateHeaderRow(key, value);
}

function resizeBoard () {
    if (!board) return;
    board.resize();
}

window.addEventListener('resize', resizeBoard);
window.addEventListener('orientationchange', resizeBoard);

document.getElementById('add-header-button').onclick = () => {
    createHeader();
}

// Board manipulation buttons
document.getElementById('to-start').onclick = () => {
    toStart();
    updateStatus();
    updateMoveText();
}

document.getElementById('to-end').onclick = () => {
    toEnd();
    updateStatus();
    updateMoveText();
}

nextMoveButton.onclick = () => {
    nextMove();
    updateStatus();
    updateMoveText();
}

previousMoveButton.onclick = () => {
    prevMove();
    updateStatus();
    updateMoveText();
}

document.getElementById('flip-board').onclick = () => {
    board.flip();
}

document.getElementById('undo-move').onclick = () => {
    undoMove();
}

document.getElementById('board-settings-button').onclick = () => {
    $('#board-settings-modal').modal('show');
}

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
            generateFromPgn(e.target.result);
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
    clearMoveList();
    createCommonHeaders();
    updateStatus();
}

document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector('form');
    if (!form) return;
    form.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
        }
    });

    form.addEventListener("submit", (event) => {
        const moveCount = game.history().length;

        if (moveCount < 10) {
            const confirmed = confirm(`This game has less than 10 moves. Are you sure you want to submit?`);

            if (!confirmed) {
                event.preventDefault();
            }
        }

    });
});

document.addEventListener('DOMContentLoaded', () => {
    const boardWrapper = document.getElementById('board-wrapper');
    const boardEl = document.getElementById('board');
    if (!boardWrapper) return;

    const observer = new ResizeObserver(() => {
        resizeBoard();
    })

    observer.observe(boardWrapper);

    let activeTouchCount = 0;
    boardEl.addEventListener('touchstart', (event) => {
        activeTouchCount = event.touches.length;

        // One finger, treat as board interaction
        if (activeTouchCount === 1) {
            event.preventDefault();
        }
    }, { passive: false });

    boardEl.addEventListener('touchmove', (event) => {
        activeTouchCount = event.touches.length;

        // One finger, prevent board from scrolling
        // Two or more allow the browser to scroll
        if (activeTouchCount === 1) {
            event.preventDefault();
        }
    })

    boardEl.addEventListener('touchend', (event) => {
        activeTouchCount = event.touches.length;
    })

    boardEl.addEventListener('touchcancel', (event) => {
        activeTouchCount = event.touches.length;
    })
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

document.getElementById('share-to-discord-accordion').addEventListener('show.bs.collapse', (e) => {
    document.getElementById('id_share_to_discord').value = "True"
    document.getElementById('share-to-discord-icon').classList.remove('bi-x-lg')
    document.getElementById('share-to-discord-icon').classList.add('bi-check-lg')
});

document.getElementById('share-to-discord-accordion').addEventListener('hide.bs.collapse', (e) => {
    document.getElementById('id_share_to_discord').value = "False"
    document.getElementById('share-to-discord-icon').classList.remove('bi-check-lg')
    document.getElementById('share-to-discord-icon').classList.add('bi-x-lg')
});

let pieceBaseUrl = $board.data('piece-url')
// Google api will add extraneous query parameters which chessboardjs does not expect
if (pieceBaseUrl) {
    pieceBaseUrl = pieceBaseUrl.split('?')[0];
}

game = new Chess();
setHeaderCallback(updateStatus);
setMoveTextCallback(updateStatus);
setClickMoveFromListFn('go-to')
setDeleteMoveFromListFn(() => {game.undo();})
board = Chessboard('board', {
    draggable: document.getElementById('id_draggable_pieces').checked,
    position: 'start',
    onDragStart: onDragStart,
    onDrop: onDrop,
    onSnapEnd: onSnapEnd,
    pieceTheme: pieceBaseUrl + '{piece}.png',
});

setBoardEventConfig({
    game,
    moveTextObj: {
        ply: 0,
        getPly: getPly,
        nextMove: nextMove,
        updateMoveText: updateMoveText,
    },
    headerObj: {
        updateHeader: updateHeader,
    },
    callback: updateStatus,
});

createCommonHeaders();
resizeBoard();
updateStatus();
