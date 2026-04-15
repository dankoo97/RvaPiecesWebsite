const moveList = document.getElementById("move-list");
let ply = 0;
let callback = () => {};
let clickMoveFromListFn = null;

export function updateMoveText (...newMoves) {
    let allMoves = Array.from(moveList.querySelectorAll('.move-text'));
    allMoves.forEach(el => el.classList.remove('current-position'));

    if (newMoves.length > 0) {
        for (const newMove of newMoves) {
            const el = createSinglePlyMoveText(newMove, allMoves.length + 1);
            allMoves.push(el);
        }
    }

    if (ply > 0) {
        const currentMove = allMoves[ply-1];
        currentMove.classList.add('current-position');
        currentMove.scrollIntoView({behavior: 'smooth', block: 'nearest', inline: 'nearest'});
    } else {
        moveList.scrollTop = 0;
    }
}

export function createSinglePlyMoveText (newMove, moveNumber) {
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
                callback();
            }
            break;
        default:
            clickMoveFromListFn = null;
    }
    moveList.addEventListener('click', clickMoveFromListFn);
}
