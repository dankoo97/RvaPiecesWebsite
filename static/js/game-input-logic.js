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
    undoLastMove,
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

function resizeBoard () {
    const boardElement = document.getElementById('board');
    if (!boardElement) return;

    const size = Math.min(window.innerWidth - 16, 600);
    boardElement.style.width = `${size}px`;
    boardElement.style.height = `${size}px`;
    board.resize();
}
window.addEventListener('resize orientationchange', resizeBoard);

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

let pieceBaseUrl = $board.data('piece-url')
// Google api will add extraneous query parameters which chessboardjs does not expect
if (pieceBaseUrl) {
    pieceBaseUrl = pieceBaseUrl.split('?')[0];
}

game = new Chess();
setHeaderCallback(updateStatus);
setMoveTextCallback(updateStatus);
setClickMoveFromListFn('go-to')
board = Chessboard('board', {
    draggable: true,
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
