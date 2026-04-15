let config = {};
let selectedSquare = null;

export function setConfig(options) {
    if (options.game) config.game = options.game;
    if (options.moveTextObj) config.moveTextObj = options.moveTextObj;
    if (options.headerObj) config.headerObj = options.headerObj;
    if (options.callback) config.callback = options.callback;
}

export function onDragStart (source, piece, position, orientation) {
    // Check if the game is over
    if (config.game.isGameOver()) return false;

    // Check if the piece is a valid piece for the current turn
    if ((config.moveTextObj.getPly() % 2 === 0 && piece.search(/^b/) !== -1) || config.moveTextObj.getPly() % 2 === 1 && piece.search(/^w/) !== -1) {
        return false;
    }
}

export function onDrop (source, target) {
    let move = null;

    if (source === target) {
        setSelectedSquare(document.getElementsByClassName("square-"+source)[0]);
        return 'snapback';
    }

    try {
        // Prevent creating moves when the board does not appear at the most recent position
        const history = config.game.history({verbose:true});
        if (config.moveTextObj.getPly() === history.length){
            move = config.game.move({
                from: source,
                to: target,
                promotion: 'q'
            });
            // Recreating historical move
        } else if (history[config.moveTextObj.getPly()]?.from === source && history[config.moveTextObj.getPly()]?.to === target){
            config.moveTextObj.nextMove();
            config.callback();
            config.moveTextObj.updateMoveText();
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

    if (config.game.isGameOver()) {
        if (config.game.isDraw()) {
            config.headerObj.updateHeader('Result', '1/2-1/2');
            if (config.game.isStalemate()) {
                config.headerObj.updateHeader('Termination', 'Stalemate');
            } else if (config.game.isThreefoldRepetition()) {
                config.headerObj.updateHeader('Termination', 'Threefold repetition');
            } else if (config.game.isDrawByFiftyMoves()) {
                config.headerObj.updateHeader('Termination', 'Draw by fifty moves');
            } else if (config.game.isInsufficientMaterial()) {
                config.headerObj.updateHeader('Termination', 'Insufficient material');
            }
        } else if (config.game.turn() === 'b') {
            config.headerObj.updateHeader('Result', '1-0');
        } else if (config.game.turn() === 'w') {
            config.headerObj.updateHeader('Result', '0-1');
        }
    }

    config.moveTextObj.nextMove();
    config.callback();
    config.moveTextObj.updateMoveText(move);
}

export function onSnapEnd () {
    config.callback(false);
}

function setSelectedSquare(square) {
    removeSelectedSquare();
    square.classList.add('selected-square');
    selectedSquare = square;
}

function removeSelectedSquare() {
    selectedSquare?.classList.remove('selected-square');
    selectedSquare = null;
}

document.getElementById('board').addEventListener('mouseup', function(e) {
    const squareEl = e.target.closest('.square-55d63');
    const square = squareEl?.dataset.square;
    if (square) {
        if (selectedSquare && onDrop(selectedSquare.dataset.square, square) !== 'snapback') {
            removeSelectedSquare();
        } else if (squareEl.children.length > 0) {
            setSelectedSquare(squareEl);
        }
        config.callback(true);
    }
})
