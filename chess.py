"""
Chess - Play in Person (Python + Tkinter)
Run with:  python chess.py      (Tkinter comes built into Python)
Click a piece to see its legal moves, click a highlighted square to move.
"""
import tkinter as tk

# ===== DATA =====
# board[row][col] is None (empty) or a 2-letter string like "wP" = white pawn.
# Colour: w/b.  Piece: K King, Q Queen, R Rook, B Bishop, N Knight, P Pawn.
# Row 0 is the top (black side), row 7 is the bottom (white side).
START = ["rnbqkbnr", "pppppppp", "........", "........",
         "........", "........", "PPPPPPPP", "RNBQKBNR"]
GLYPH = {"K": "♚", "Q": "♛", "R": "♜", "B": "♝", "N": "♞", "P": "♟"}
SQ = 72  # size of one square in pixels


def inside(r, c):
    """Is this square on the board?"""
    return 0 <= r < 8 and 0 <= c < 8


# ===== MOVE RULES =====
# A move is a tuple (row, col, flag). flag is None, "ep" (en passant),
# "K" (castle kingside) or "Q" (castle queenside).
def raw_moves(b, r, c, castle, ep, attack_only=False):
    """Where a piece could go by its movement rules, ignoring whether
    it leaves its own king in danger. attack_only=True returns the
    squares the piece attacks (used to detect check)."""
    p = b[r][c]
    col, t = p[0], p[1]
    out = []

    def enemy(rr, cc):
        return b[rr][cc] is not None and b[rr][cc][0] != col

    if t == "P":  # PAWN
        d = -1 if col == "w" else 1          # white moves up, black moves down
        start = 6 if col == "w" else 1
        for dc in (-1, 1):                   # diagonals: captures only
            rr, cc = r + d, c + dc
            if not inside(rr, cc):
                continue
            if attack_only or enemy(rr, cc):
                out.append((rr, cc, None))
            elif ep == (rr, cc):             # en passant
                out.append((rr, cc, "ep"))
        if not attack_only and inside(r + d, c) and b[r + d][c] is None:
            out.append((r + d, c, None))     # one step forward
            if r == start and b[r + 2 * d][c] is None:
                out.append((r + 2 * d, c, None))  # two steps on first move

    elif t in "NK":  # KNIGHT and KING: fixed jumps
        jumps = ([(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
                 if t == "N" else
                 [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)])
        for dr, dc in jumps:
            rr, cc = r + dr, c + dc
            if inside(rr, cc) and (b[rr][cc] is None or enemy(rr, cc)):
                out.append((rr, cc, None))
        if t == "K" and not attack_only:     # CASTLING
            row, opp = (7, "b") if col == "w" else (0, "w")
            if r == row and c == 4 and not attacked(b, row, 4, opp):
                if (castle[col + "K"] and b[row][5] is None and b[row][6] is None
                        and not attacked(b, row, 5, opp) and not attacked(b, row, 6, opp)):
                    out.append((row, 6, "K"))
                if (castle[col + "Q"] and b[row][1] is None and b[row][2] is None
                        and b[row][3] is None
                        and not attacked(b, row, 3, opp) and not attacked(b, row, 2, opp)):
                    out.append((row, 2, "Q"))

    else:  # ROOK, BISHOP, QUEEN: slide until something blocks the way
        straight = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        diagonal = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        dirs = straight if t == "R" else diagonal if t == "B" else straight + diagonal
        for dr, dc in dirs:
            rr, cc = r + dr, c + dc
            while inside(rr, cc):
                if b[rr][cc] is None:
                    out.append((rr, cc, None))       # empty: keep sliding
                else:
                    if enemy(rr, cc):
                        out.append((rr, cc, None))   # capture, then stop
                    break                            # blocked
                rr, cc = rr + dr, cc + dc
    return out


def attacked(b, r, c, by_col):
    """Is square (r, c) attacked by any piece of colour by_col?"""
    for i in range(8):
        for j in range(8):
            if b[i][j] and b[i][j][0] == by_col:
                if any(m[0] == r and m[1] == c for m in raw_moves(b, i, j, None, None, True)):
                    return True
    return False


def in_check(b, col):
    """Is the king of this colour currently in check?"""
    for i in range(8):
        for j in range(8):
            if b[i][j] == col + "K":
                return attacked(b, i, j, "b" if col == "w" else "w")
    return False


def apply_move(b, fr, fc, m):
    """Play a move on a COPY of the board (so we can test moves safely)."""
    nb = [row[:] for row in b]
    r, c, flag = m
    piece = nb[fr][fc]
    nb[r][c], nb[fr][fc] = piece, None
    if flag == "ep":
        nb[fr][c] = None                     # remove the pawn that was passed
    if flag == "K":
        nb[r][5], nb[r][7] = nb[r][7], None  # move the rook too
    if flag == "Q":
        nb[r][3], nb[r][0] = nb[r][0], None
    if piece[1] == "P" and r in (0, 7):
        nb[r][c] = piece[0] + "Q"            # promotion: pawn becomes a Queen
    return nb


def legal_moves(b, r, c, castle, ep):
    """Legal = raw moves that do not leave your own king in check."""
    col = b[r][c][0]
    return [m for m in raw_moves(b, r, c, castle, ep)
            if not in_check(apply_move(b, r, c, m), col)]


def has_any_move(b, col, castle, ep):
    return any(b[i][j] and b[i][j][0] == col and legal_moves(b, i, j, castle, ep)
               for i in range(8) for j in range(8))


# ===== THE WINDOW (GUI) =====
class ChessApp:
    def __init__(self, root):
        root.title("Chess - Play in Person")
        self.status = tk.Label(root, font=("Arial", 16, "bold"))
        self.status.pack(pady=6)
        self.canvas = tk.Canvas(root, width=8 * SQ, height=8 * SQ)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)   # mouse click / touch
        tk.Button(root, text="New Game", command=self.new_game).pack(pady=6)
        self.new_game()

    def new_game(self):
        # Turn the text rows into the board array
        self.board = [[None if ch == "." else ("b" if ch.islower() else "w") + ch.upper()
                       for ch in row] for row in START]
        self.turn = "w"
        self.castle = {"wK": 1, "wQ": 1, "bK": 1, "bQ": 1}  # castling rights left
        self.ep = None          # en passant target square
        self.selected = None    # currently selected piece
        self.moves = []         # its legal moves
        self.over = False
        self.draw()

    def on_click(self, event):
        """What happens when a player clicks a square."""
        if self.over:
            return
        r, c = event.y // SQ, event.x // SQ
        if not inside(r, c):
            return
        move = next((m for m in self.moves if m[0] == r and m[1] == c), None)
        if self.selected and move:                    # clicked a highlighted square: move
            self.make_move(move)
            return
        if self.board[r][c] and self.board[r][c][0] == self.turn:   # clicked own piece: select
            self.selected = (r, c)
            self.moves = legal_moves(self.board, r, c, self.castle, self.ep)
        else:
            self.selected, self.moves = None, []
        self.draw()

    def make_move(self, m):
        fr, fc = self.selected
        piece = self.board[fr][fc]
        # Update castling rights if king/rook moved or a rook was captured
        if piece[1] == "K":
            self.castle[self.turn + "K"] = self.castle[self.turn + "Q"] = 0
        for (rr, cc, key) in [(7, 0, "wQ"), (7, 7, "wK"), (0, 0, "bQ"), (0, 7, "bK")]:
            if (fr, fc) == (rr, cc) or (m[0], m[1]) == (rr, cc):
                self.castle[key] = 0
        # Remember en passant square if a pawn just moved two squares
        self.ep = ((m[0] + fr) // 2, fc) if piece[1] == "P" and abs(m[0] - fr) == 2 else None
        self.board = apply_move(self.board, fr, fc, m)
        self.turn = "b" if self.turn == "w" else "w"  # switch players
        self.selected, self.moves = None, []
        self.draw()

    def draw(self):
        """Redraw the board, highlights, pieces and status text."""
        cv = self.canvas
        cv.delete("all")
        check = in_check(self.board, self.turn)
        for r in range(8):
            for c in range(8):
                x, y = c * SQ, r * SQ
                colour = "#b58863" if (r + c) % 2 else "#f0d9b5"
                if self.selected == (r, c):
                    colour = "#f6f669"                        # selected piece
                if check and self.board[r][c] == self.turn + "K":
                    colour = "#ff6b6b"                        # king in check
                cv.create_rectangle(x, y, x + SQ, y + SQ, fill=colour, width=0)
                mv = next((m for m in self.moves if m[0] == r and m[1] == c), None)
                if mv:                                        # possible move marker
                    if self.board[r][c] or mv[2] == "ep":     # capture: ring
                        cv.create_oval(x + 5, y + 5, x + SQ - 5, y + SQ - 5, outline="#555", width=4)
                    else:                                     # empty square: dot
                        cv.create_oval(x + 26, y + 26, x + SQ - 26, y + SQ - 26, fill="#666", width=0)
                p = self.board[r][c]
                if p:
                    cx, cy = x + SQ // 2, y + SQ // 2
                    fill = "white" if p[0] == "w" else "black"
                    if p[0] == "w":                           # black outline for white pieces
                        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                            cv.create_text(cx + dx, cy + dy, text=GLYPH[p[1]], font=("Arial", 44), fill="black")
                    cv.create_text(cx, cy, text=GLYPH[p[1]], font=("Arial", 44), fill=fill)
        # Game end: no legal moves = checkmate (if in check) or stalemate (draw)
        name = "White" if self.turn == "w" else "Black"
        text = f"{name} to move"
        if not has_any_move(self.board, self.turn, self.castle, self.ep):
            self.over = True
            text = (f"Checkmate! {'Black' if self.turn == 'w' else 'White'} wins!"
                    if check else "Stalemate - draw!")
        elif check:
            text = f"{name} is in CHECK!"
        self.status.config(text=text)


if __name__ == "__main__":
    root = tk.Tk()
    ChessApp(root)
    root.mainloop()
