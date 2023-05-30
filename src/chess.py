# выполненные доп. задачи: 4, 5, 7, 8, 9
# также перед выбором фигур подсвечиваются те, которыми можно ходить
# и автоматически определяются шах и пат

from copy import deepcopy
from enum import Enum, auto
from reprint import output
try:
    import msvcrt
except ImportError:
    UNIX = True
    import sys
    import tty
    import termios
else:
    UNIX = False

INITIAL_BOARD = [['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R'],
                 ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
                 ['.', '.', '.', '.', '.', '.', '.', '.'],
                 ['.', '.', '.', '.', '.', '.', '.', '.'],
                 ['.', '.', '.', '.', '.', '.', '.', '.'],
                 ['.', '.', '.', '.', '.', '.', '.', '.'],
                 ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
                 ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r']]
WHITE_STARTS = True

if UNIX:

    def getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
else:
    getch = msvcrt.getch


class Action(Enum):
    CHECK_CHECK = auto()
    FIG_FILE = auto()
    FIG_RANK = auto()
    MOV_FILE = auto()
    MOV_RANK = auto()
    PROMOTION = auto()


def write_base(out):
    out[0] = out[13] = '   a b c d e f g h'
    out[1] = out[12] = out[14] = ' '
    out[16] = ' '
    out[17] = ' '
    out[18] = ' '
    out[19] = 'ESC to go back'


def is_theirs(w, c):
    if w:
        return c.isupper()
    return c.islower()


FILES = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7,\
         'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7,\
         'ф': 0, 'и': 1, 'с': 2, 'в': 3, 'у': 4, 'а': 5, 'п': 6, 'р': 7,\
         'Ф': 0, 'И': 1, 'С': 2, 'В': 3, 'У': 4, 'А': 5, 'П': 6, 'Р': 7,\
         }

FALSES = [[False for j in range(8)] for i in range(8)]


def moves(board, rank, file, w):
    poses = []
    fig = board[rank][file]
    if fig in ('r', 'R', 'q', 'Q'):
        for d in (((r, file) for r in range(rank - 1, -1, -1)),
                  ((r, file) for r in range(rank + 1, 8)),
                  ((rank, f) for f in range(file - 1, -1, -1)),
                  ((rank, f) for f in range(file + 1, 8))):
            for r, f in d:
                if is_theirs(w, board[r][f]):
                    break
                poses.append((r, f))
                if board[r][f] != '.':
                    break
    elif fig in ('n', 'N'):
        poses = [
            (r, f) for r, f in ((rank - 2, file - 1), (rank - 1, file - 2),
                                (rank - 2, file + 1), (rank - 1, file + 2),
                                (rank + 2, file - 1), (rank + 1, file - 2),
                                (rank + 2, file + 1), (rank + 1, file + 2))
            if 0 <= r < 8 and 0 <= f < 8 and not is_theirs(w, board[r][f])
        ]
    elif fig in ('p', 'P'):
        d = 1 if w else -1
        r = rank + d
        if board[r][file] == '.':
            poses.append((r, file))
            init = 1 if w else 6
            if rank == init and board[r + d][file] == '.':
                poses.append((r + d, file))
        if file < 7 and is_theirs(not w, board[r][file + 1]):
            poses.append((r, file + 1))
        if file > 0 and is_theirs(not w, board[r][file - 1]):
            poses.append((r, file - 1))
    elif fig in ('k', 'K'):
        for r in (x for x in (rank - 1, rank, rank + 1) if 0 <= x < 8):
            for f in (x for x in (file - 1, file, file + 1) if 0 <= x < 8):
                if not is_theirs(w, board[r][f]):
                    poses.append((r, f))
    if fig in ('b', 'B', 'q', 'Q'):
        for d in (((rank - 1 - i, file - 1 - i)
                   for i in range(min(rank, file))),
                  ((rank - 1 - i, file + 1 + i)
                   for i in range(min(rank, 7 - file))),
                  ((rank + 1 + i, file - 1 - i)
                   for i in range(min(7 - rank, file))),
                  ((rank + 1 + i, file + 1 + i)
                   for i in range(min(7 - rank, 7 - file)))):
            for r, f in d:
                if is_theirs(w, board[r][f]):
                    break
                poses.append((r, f))
                if board[r][f] != '.':
                    break
    return poses


def compose_msg(p, l, lm, r, rm, f):
    msg = ''
    if p[0]:
        msg += '^' + l + ' (' + lm + ')'
    if p[1]:
        if msg:
            msg += ' '
        msg += '^' + r + ' (' + rm + ')'
    if msg:
        msg = '(' + msg + ' for ' + f + ')'
    return msg


def redraw(out, board, reds, w, action, check, moves_done, cp=None, ep=None):
    for i in range(8):
        border = str(i + 1)
        line = []
        for j in range(8):
            if reds[i][j]:
                line.append('\033[31m' + board[i][j] + '\033[0m')
            else:
                line.append(board[i][j])
        out[(10 - i) if w else
            (3 + i)] = border + '  ' + ' '.join(line) + '  ' + border
    out[18] = '\033[33m(your king is in check)\033[0m' if check else ' '
    out[20] = 'moves done: ' + str(moves_done)
    if action == Action.FIG_FILE:
        out[15] = "choose figure's file (a-h)"
        out[16] = compose_msg(cp, 'L', 'queenside', 'R', 'kingside',
                              'castling') or ' '
        out[17] = compose_msg(ep, 'E', 'from left', 'P', 'from right',
                              'en passant') or ' '
    elif action == Action.FIG_RANK:
        out[15] = "choose figure's rank (1-8)"
    elif action == Action.MOV_FILE:
        out[15] = "choose new position's file (a-h)"
    elif action == Action.MOV_RANK:
        out[15] = "choose new position's rank (1-8)"
    elif action == Action.PROMOTION:
        out[15] = 'choose a piece to promote the pawn'


def check_check(board, w):
    threatened = set()
    for r in range(8):
        for f in range(8):
            if is_theirs(not w, board[r][f]):
                threatened.update(moves(board, r, f, not w))
    for r, f in threatened:
        if board[r][f] == ('K' if w else 'k'):
            return True
    return False


def king_pass_check(possible, to_check, board, w, r):
    for f in to_check:
        if not possible or board[r][f] != '.':
            return False
        check_board = deepcopy(board)
        check_board[r][f] = 'K' if w else 'k'
        check_board[r][4] = '.'
        possible = possible and not check_check(check_board, w)
    return possible


def castling_possible(board, w, rook_or_king_not_moved, check):
    r = 0 if w else 7
    left = not check and rook_or_king_not_moved[(r, 4)]\
                     and rook_or_king_not_moved[(r, 0)]
    left = king_pass_check(left, (3, 2), board, w, r)
    right = not check and rook_or_king_not_moved[(r, 4)]\
                      and rook_or_king_not_moved[(r, 7)]
    right = king_pass_check(right, (5, 6), board, w, r)
    return (left, right)


def get_allowed_moves(board, w):
    allowed_moves = {}
    for r in range(8):
        for f in range(8):
            allowed_moves[(r, f)] = []
            if is_theirs(w, board[r][f]):
                ms = moves(board, r, f, w)
                for r2, f2 in ms:
                    check_board = deepcopy(board)
                    check_board[r2][f2] = check_board[r][f]
                    check_board[r][f] = '.'
                    if not check_check(check_board, w):
                        allowed_moves[(r, f)].append((r2, f2))
    return allowed_moves


def main():
    w = WHITE_STARTS
    file = 0
    mfile = 0
    rank = 0
    cp = (0, 0)
    c = ''
    check = False
    moves_done = 0
    rook_or_king_not_moved = {
        x: True
        for x in ((0, 0), (0, 7), (7, 0), (7, 7), (0, 4), (7, 4))
    }
    en_passant_left = None
    en_passant_right = None
    board = INITIAL_BOARD
    old_boards = []
    docheck = True
    reds = deepcopy(FALSES)
    with output(output_type="list",
                initial_len=21,
                interval=0,
                force_single_line=True) as out:
        write_base(out)
        action = Action.CHECK_CHECK
        redraw(out, board, reds, w, action, check, moves_done)
        if check_check(board, not w):
            out[15] = 'This is an impossible situation, exiting...'
            exit()
        while True:
            if action == Action.CHECK_CHECK:
                if docheck:
                    allowed_moves = get_allowed_moves(board, w)
                    check = check_check(board, w)
                    no_moves = not any(len(x) for x in allowed_moves.values())
                    if no_moves:
                        out[15] = (('BLACK' if w else 'WHITE') +
                                   ' WON') if check else 'STALEMATE'
                        exit()
                    cp = castling_possible(board, w, rook_or_king_not_moved,
                                           check)
                    ep = (en_passant_left, en_passant_right)
                else:
                    docheck = True
                for ((r, f), ms) in allowed_moves.items():
                    if ms:
                        reds[r][f] = True
                action = Action.FIG_FILE
                redraw(out, board, reds, w, action, check, moves_done, cp, ep)
            c = getch()
            if c in '\3\4':  # ^C^D
                out[15] = 'Exiting...'
                exit()
            if c == '[':
                # arrow keys result in character sequences like '\x1b' '[' 'D'
                getch()
                continue
            if action == Action.FIG_FILE:
                if c == '\x1b':  # ESC
                    if not old_boards:
                        continue
                    reds = deepcopy(FALSES)
                    board, en_passant_left, en_passant_right = old_boards.pop()
                    moves_done -= 1
                    w = not w
                    action = Action.CHECK_CHECK
                    continue
                if c in '\f\x12':  # ^L^R
                    if not (c == '\f' and cp[0] or c == '\x12' and cp[1]):
                        continue
                    reds = deepcopy(FALSES)
                    old_boards.append(
                        (deepcopy(board), en_passant_left, en_passant_right))
                    r = 0 if w else 7
                    board[r][4] = '.'
                    board[r][2 if c == '\f' else 6] = 'K' if w else 'k'
                    board[r][0 if c == '\f' else 7] = '.'
                    board[r][3 if c == '\f' else 5] = 'R' if w else 'r'
                    moves_done += 1
                    w = not w
                    action = Action.CHECK_CHECK
                    continue
                if c in '\5\x10':  # ^E^P
                    if not (c == '\5' and en_passant_left
                            or c == '\x10' and en_passant_right):
                        continue
                    reds = deepcopy(FALSES)
                    old_boards.append(
                        (deepcopy(board), en_passant_left, en_passant_right))
                    epd = en_passant_left if c == '\5' else en_passant_right
                    ((r, f), (r1, f1), (r2, f2)) = epd
                    board[r1][f1] = board[r][f]
                    board[r][f] = '.'
                    board[r2][f2] = '.'
                    en_passant_left = None
                    en_passant_right = None
                    moves_done += 1
                    w = not w
                    action = Action.CHECK_CHECK
                    continue
                file = FILES.get(c)
                if file is None:
                    continue
                poses = []
                for r in range(8):
                    if reds[r][file]:
                        poses.append((r, file))
                if not poses:
                    continue
                reds = deepcopy(FALSES)
                for r, f in poses:
                    reds[r][f] = True
                action = Action.FIG_RANK
                redraw(out, board, reds, w, action, check, moves_done)
            elif action == Action.FIG_RANK:
                if c == '\x1b':  # ESC
                    reds = deepcopy(FALSES)
                    docheck = False
                    action = Action.CHECK_CHECK
                    redraw(out, board, reds, w, action, check, moves_done, cp,
                           ep)
                    continue
                if c not in ('1', '2', '3', '4', '5', '6', '7', '8'):
                    continue
                rank = int(c) - 1
                if not reds[rank][file]:
                    continue
                reds = deepcopy(FALSES)
                for r, f in allowed_moves[(rank, file)]:
                    reds[r][f] = True
                action = Action.MOV_FILE
                redraw(out, board, reds, w, action, check, moves_done)
            elif action == Action.MOV_FILE:
                if c == '\x1b':  # ESC
                    reds = deepcopy(FALSES)
                    docheck = False
                    action = Action.CHECK_CHECK
                    redraw(out, board, reds, w, action, check, moves_done, cp,
                           ep)
                    continue
                mfile = FILES.get(c)
                if mfile is None:
                    continue
                poses = []
                for r in range(8):
                    if reds[r][mfile]:
                        poses.append((r, mfile))
                if not poses:
                    continue
                reds = deepcopy(FALSES)
                for r, f in poses:
                    reds[r][f] = True
                action = Action.MOV_RANK
                redraw(out, board, reds, w, action, check, moves_done)
            elif action == Action.MOV_RANK:
                if c == '\x1b':  # ESC
                    reds = deepcopy(FALSES)
                    docheck = False
                    action = Action.CHECK_CHECK
                    redraw(out, board, reds, w, action, check, moves_done, cp,
                           ep)
                    continue
                if c not in ('1', '2', '3', '4', '5', '6', '7', '8'):
                    continue
                mrank = int(c) - 1
                if not reds[mrank][mfile]:
                    continue
                reds = deepcopy(FALSES)
                old_boards.append(
                    (deepcopy(board), en_passant_left, en_passant_right))
                if board[rank][file] in ('r', 'R', 'k', 'K'):
                    if (rank, file) in rook_or_king_not_moved:
                        rook_or_king_not_moved[(rank, file)] = False
                board[mrank][mfile] = board[rank][file]
                board[rank][file] = '.'
                en_passant_left = None
                en_passant_right = None
                p = ('P' if w else 'p')
                if board[mrank][mfile] == p:
                    if abs(mrank - rank) == 2:
                        op = 'p' if w else 'P'
                        d = 1 if w else -1
                        if mfile > 0 and board[mrank][mfile - 1] == op:
                            en_passant_left = ((mrank, mfile - 1),\
                                               (rank + d, mfile),\
                                               (mrank, mfile))
                        if mfile < 7 and board[mrank][mfile + 1] == op:
                            en_passant_right = ((mrank, mfile + 1),\
                                                (rank + d, mfile),\
                                                (mrank, mfile))
                    elif mrank == (7 if w else 0):
                        reds[mrank][mfile] = True
                        promoted = ((mrank, mfile))
                        action = Action.PROMOTION
                        redraw(out, board, reds, w, action, check, moves_done)
                        continue
                moves_done += 1
                w = not w
                action = Action.CHECK_CHECK
                redraw(out, board, reds, w, action, check, moves_done)
            elif action == Action.PROMOTION:
                if c == '\x1b':  # ESC
                    reds = deepcopy(FALSES)
                    board, en_passant_left, en_passant_right = old_boards.pop()
                    action = Action.CHECK_CHECK
                    continue
                if c not in ('Q', 'q', 'N', 'n', 'R', 'r', 'B', 'b'):
                    continue
                reds = deepcopy(FALSES)
                c = c.upper() if w else c.lower()
                r, f = promoted
                board[r][f] = c
                moves_done += 1
                w = not w
                action = Action.CHECK_CHECK
                redraw(out, board, reds, w, action, check, moves_done)


if __name__ == '__main__':
    main()
