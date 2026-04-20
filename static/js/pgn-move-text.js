const moveList = document.getElementById("move-list");
let ply = 0;
let callback = () => {};
let clickMoveFromListFn = null;
let deleteMoveFromListFn = null;

const moveTextTableView = () => document.getElementById('id_move_table_view').checked;

const contextMenu = document.getElementById('move-list-menu');
let contextMenuIndex = null;

export function updateMoveText (...newMoves) {
    let allMoves = Array.from(moveList.querySelectorAll('.move-text'));
    allMoves.forEach(el => el.classList.remove('current-position'));

    if (newMoves.length > 0) {
        for (const newMove of newMoves) {
            const el = createSinglePlyMoveText(newMove, allMoves.length + 1);
            allMoves.push(el);
        }
    }

    setCurrentPositionCls();
}

export function setCurrentPositionCls () {
    let allMoves = Array.from(moveList.querySelectorAll('.move-text'));
    if (ply > 0) {
        const currentMove = allMoves[ply-1];
        currentMove.classList.add('current-position');
    }
}

export function createSinglePlyMoveText (newMove, moveNumber) {
    let newMoveEl = document.createElement('div');
    let moveText = newMove.san;
    if (moveNumber % 2 === 1) {
        newMoveEl.innerHTML = `${Math.floor(moveNumber/2) + 1}. ${moveText}`;
    } else {
        newMoveEl.innerHTML = moveText;
    }
    newMoveEl.classList.add('move-text', 'mx-1', 'rounded-2', 'px-1');
    moveList.appendChild(newMoveEl);

    return newMoveEl;
}

export function undoLastMove () {
    if (ply === 0) return;
    let allMoves = Array.from(moveList.querySelectorAll('.move-text'));
    let lastMove = allMoves.pop();
    if (allMoves.length % 2 === 0) {
        moveList.removeChild(moveList.lastChild);
    } else {
        lastMove.remove();
    }
    toEnd();
    updateMoveText();
    setCurrentPositionCls();
    callback();
}

export function setPly(n) {
    ply = n;
}

export function getPly() {
    return ply;
}

export function toStart() {
    ply = 0;
}

export function toEnd() {
    ply = moveList.querySelectorAll('.move-text').length;
}

export function nextMove() {
    ply++;
}

export function prevMove() {
    ply--;
}

export function clearMoveList() {
    moveList.innerHTML = "";
    toStart();
}

export function setCallback(cb) {
    callback = cb;
}

export function setClickMoveFromListFn(fn) {
    moveList.removeEventListener('click', clickMoveFromListFn);
    if (typeof fn === 'function') {
        clickMoveFromListFn = fn;
        moveList.addEventListener('click', clickMoveFromListFn);
        return;
    }

    switch (fn) {
        case 'go-to':
            clickMoveFromListFn = (event) => {
                const move = event.target;
                if (move.classList.contains('move-text')) {
                    setPly(Array.from(moveList.querySelectorAll('.move-text')).indexOf(move) + 1);
                    updateMoveText();
                }
                setCurrentPositionCls();
                callback();
            }
            break;
        default:
            clickMoveFromListFn = null;
    }
    moveList.addEventListener('click', clickMoveFromListFn);
}

export function setDeleteMoveFromListFn(fn) {
    deleteMoveFromListFn = fn;
}

function deleteMoveFromHere(moveIndex) {
    const allMoves = Array.from(moveList.querySelectorAll('.move-text'));
    while (allMoves.length > moveIndex) {
        allMoves.pop().remove();
        deleteMoveFromListFn();
    }
    toEnd();
    setCurrentPositionCls();
}

function showContextMenu(x, y, moveIndex) {
    contextMenuIndex = moveIndex;
    contextMenu.style.left = `${x + window.scrollX}px`;
    contextMenu.style.top = `${y + window.scrollY}px`;
    contextMenu.classList.toggle('show');
}

function hideContextMenu() {
    contextMenu.classList.remove('show');
    contextMenuIndex = null;
}

document.getElementById('id_move_table_view').addEventListener('change', () => {
    moveList.classList.toggle('move-list--table', moveTextTableView());
    moveList.classList.toggle('move-list--inline', !moveTextTableView());
});

moveList.addEventListener('contextmenu', (event) => {
    const move = event.target.closest('.move-text');
    if (!move) return;

    event.preventDefault();
    const moveIndex = Array.from(moveList.querySelectorAll('.move-text')).indexOf(move);
    showContextMenu(event.clientX, event.clientY, moveIndex);
});

document.addEventListener('click', hideContextMenu);
document.addEventListener('scroll', hideContextMenu);
window.addEventListener('resize', hideContextMenu);
document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') hideContextMenu();
});

document.getElementById('delete-from-here-button').addEventListener('click', () => {
    if (contextMenuIndex === null) return;
    deleteMoveFromHere(contextMenuIndex);
    hideContextMenu();
    callback();
})
