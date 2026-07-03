import os
import sys
import threading
import pygame
 
from game import board, pawn, knight, bishop, rook, queen, king
from bot import bot as compute_bot_move
 
pygame.init()
 
# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SQUARE_SIZE = 80
BOARD_PIXELS = SQUARE_SIZE * 8
SIDE_PANEL_WIDTH = 200
FLIP_DELAY_MS = 600  # pause before the board auto-flips after a move
BOT_DEPTH = 2  # minimax search depth for the bot (see bot.py -- depth 3+ is very slow, no pruning)
WINDOW_WIDTH = BOARD_PIXELS + SIDE_PANEL_WIDTH
WINDOW_HEIGHT = BOARD_PIXELS
 
ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
 
LIGHT_SQUARE = (238, 216, 192)
DARK_SQUARE = (170, 120, 90)
SELECT_COLOR = (246, 210, 90)
MOVE_DOT_COLOR = (60, 60, 60)
CAPTURE_RING_COLOR = (200, 60, 60)
CHECK_COLOR = (220, 70, 70)
PANEL_BG = (35, 35, 38)
TEXT_COLOR = (235, 235, 235)
BUTTON_COLOR = (70, 70, 76)
BUTTON_HOVER_COLOR = (95, 95, 102)
LAST_MOVE_COLOR = (170, 200, 100)
 
FONT = pygame.font.SysFont("segoeui", 22)
FONT_BIG = pygame.font.SysFont("segoeui", 26, bold=True)
FONT_SMALL = pygame.font.SysFont("segoeui", 16)
 
PIECE_TYPE_ALIASES = {
    "pawn": ["pawn", "p"],
    "knight": ["knight", "n"],
    "bishop": ["bishop", "b"],
    "rook": ["rook", "r"],
    "queen": ["queen", "q"],
    "king": ["king", "k"],
}
COLOR_ALIASES = {
    "white": ["white", "w"],
    "black": ["black", "b"],
}
 
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Chess")
clock = pygame.time.Clock()
 
 
# ---------------------------------------------------------------------------
# Asset loading (tries a handful of common naming conventions, falls back to
# drawing a simple shape + letter if nothing is found)
# ---------------------------------------------------------------------------
def load_piece_images():
    images = {}
    if not os.path.isdir(ASSET_DIR):
        print(f"[warning] No 'assets' folder found at {ASSET_DIR}, using fallback shapes for all pieces.")
        return images
 
    for color, color_names in COLOR_ALIASES.items():
        for ptype, type_names in PIECE_TYPE_ALIASES.items():
            found_path = None
            for cname in color_names:
                for tname in type_names:
                    for sep in ["_", "-", ""]:
                        for ext in [".png", ".PNG", ".webp"]:
                            candidate = os.path.join(ASSET_DIR, f"{cname}{sep}{tname}{ext}")
                            if os.path.exists(candidate):
                                found_path = candidate
                                break
                        if found_path:
                            break
                    if found_path:
                        break
                if found_path:
                    break
 
            if found_path:
                try:
                    img = pygame.image.load(found_path).convert_alpha()
                    img = pygame.transform.smoothscale(img, (SQUARE_SIZE - 12, SQUARE_SIZE - 12))
                    images[(color, ptype)] = img
                except pygame.error as e:
                    print(f"[warning] Failed to load {found_path}: {e}")
                    images[(color, ptype)] = None
            else:
                images[(color, ptype)] = None
                print(f"[warning] No sprite found for {color} {ptype}, using fallback shape.")
 
    return images
 
 
PIECE_IMAGES = load_piece_images()
 
FALLBACK_LABELS = {
    "pawn": "P", "knight": "N", "bishop": "B",
    "rook": "R", "queen": "Q", "king": "K",
}
 
 
def draw_fallback_piece(surface, color, ptype, center):
    radius = SQUARE_SIZE // 2 - 10
    fill = (250, 250, 250) if color == "white" else (35, 35, 35)
    outline = (20, 20, 20) if color == "white" else (230, 230, 230)
    pygame.draw.circle(surface, fill, center, radius)
    pygame.draw.circle(surface, outline, center, radius, 2)
    label = FONT_BIG.render(FALLBACK_LABELS[ptype], True, outline)
    surface.blit(label, label.get_rect(center=center))
 
 
def draw_piece(surface, piece_obj, center):
    img = PIECE_IMAGES.get((piece_obj.color, piece_obj.type))
    if img:
        surface.blit(img, img.get_rect(center=center))
    else:
        draw_fallback_piece(surface, piece_obj.color, piece_obj.type, center)
 
 
# ---------------------------------------------------------------------------
# Board <-> screen coordinate helpers (board[0] is the black back rank,
# board[7] is the white back rank; "flipped" swaps which side is at the
# bottom of the window)
# ---------------------------------------------------------------------------
def board_to_screen(row, col, flipped):
    if flipped:
        return (7 - col) * SQUARE_SIZE, (7 - row) * SQUARE_SIZE
    return col * SQUARE_SIZE, row * SQUARE_SIZE
 
 
def screen_to_board(x, y, flipped):
    if not (0 <= x < BOARD_PIXELS and 0 <= y < BOARD_PIXELS):
        return None
    sc, sr = x // SQUARE_SIZE, y // SQUARE_SIZE
    if flipped:
        return (7 - sr, 7 - sc)
    return (sr, sc)
 
 
# ---------------------------------------------------------------------------
# Move legality helpers (filters out moves that would leave your own king
# in check -- the base rules module only computes raw piece movement)
# ---------------------------------------------------------------------------
def king_position_after(game, start, end, moving_piece, white_king_pos, black_king_pos):
    if isinstance(moving_piece, king):
        if moving_piece.color == "white":
            return end, black_king_pos
        return white_king_pos, end
    return white_king_pos, black_king_pos
 
 
def is_square_attacked(grid, target_pos, by_color):
    for r in range(8):
        for c in range(8):
            p = grid[r][c]
            if p != "" and p.color == by_color:
                if target_pos in p.get_legal_moves((r, c), grid):
                    return True
    return False
 
 
def simulate_move_grid(game, start, end):
    """Returns a shallow-copied grid with the move applied (does not
    mutate the real game state). Handles en passant capture too."""
    grid = [row[:] for row in game.board]
    moving_piece = grid[start[0]][start[1]]
    is_ep = isinstance(moving_piece, pawn) and game.en_passant(start, end)
    grid[end[0]][end[1]] = moving_piece
    grid[start[0]][start[1]] = ""
    if is_ep:
        grid[start[0]][end[1]] = ""
    return grid
 
 
def get_safe_legal_moves(game, row, col):
    """Legal moves for the piece at (row, col) that don't leave its own
    king in check."""
    piece_obj = game.board[row][col]
    if piece_obj == "":
        return []
    raw_moves = piece_obj.get_legal_moves((row, col), game.board)
    safe_moves = []
    for end in raw_moves:
        grid = simulate_move_grid(game, (row, col), end)
        wk, bk = king_position_after(
            game, (row, col), end, piece_obj,
            game.white_king_position, game.black_king_position
        )
        own_king_pos = wk if piece_obj.color == "white" else bk
        if not is_square_attacked(grid, own_king_pos, "black" if piece_obj.color == "white" else "white"):
            safe_moves.append(end)
 
    # Castling isn't part of piece.get_legal_moves() -- it's validated
    # separately in board.king_castle()/queen_castle() -- so add it here
    # if it's currently available.
    if isinstance(piece_obj, king):
        home_row = 7 if piece_obj.color == "white" else 0
        if (row, col) == (home_row, 4):
            if game.king_castle(piece_obj.color):
                safe_moves.append((home_row, 6))
            if game.queen_castle(piece_obj.color):
                safe_moves.append((home_row, 2))
 
    return safe_moves
 
 
def color_has_any_move(game, color):
    for r in range(8):
        for c in range(8):
            p = game.board[r][c]
            if p != "" and p.color == color:
                if get_safe_legal_moves(game, r, c):
                    return True
    return False
 
 
# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------
class Button:
    def __init__(self, rect, label):
        self.rect = pygame.Rect(rect)
        self.label = label
 
    def draw(self, surface):
        hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(surface, BUTTON_HOVER_COLOR if hovered else BUTTON_COLOR, self.rect, border_radius=8)
        text = FONT.render(self.label, True, TEXT_COLOR)
        surface.blit(text, text.get_rect(center=self.rect.center))
 
    def clicked(self, pos):
        return self.rect.collidepoint(pos)
 
 
flip_button = Button((BOARD_PIXELS + 25, 30, SIDE_PANEL_WIDTH - 50, 45), "Flip Board")
reset_button = Button((BOARD_PIXELS + 25, 90, SIDE_PANEL_WIDTH - 50, 45), "New Game")
play_white_button = Button((BOARD_PIXELS + 25, 150, SIDE_PANEL_WIDTH - 50, 40), "Play as White")
play_black_button = Button((BOARD_PIXELS + 25, 195, SIDE_PANEL_WIDTH - 50, 40), "Play as Black")
 
PROMOTION_CHOICES = ["queen", "rook", "bishop", "knight"]
 
 
def draw_promotion_menu(surface, color, flipped, promo_pos):
    row, col = promo_pos
    x, y = board_to_screen(row, col, flipped)
    menu_w, menu_h = SQUARE_SIZE, SQUARE_SIZE * 4
    menu_x = x
    menu_y = y if row < 4 else y - menu_h + SQUARE_SIZE
    menu_y = max(0, min(menu_y, BOARD_PIXELS - menu_h))
 
    pygame.draw.rect(surface, (245, 245, 245), (menu_x, menu_y, menu_w, menu_h))
    pygame.draw.rect(surface, (20, 20, 20), (menu_x, menu_y, menu_w, menu_h), 2)
 
    rects = []
    for i, ptype in enumerate(PROMOTION_CHOICES):
        cell_rect = pygame.Rect(menu_x, menu_y + i * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        pygame.draw.rect(surface, (255, 255, 255), cell_rect)
        img = PIECE_IMAGES.get((color, ptype))
        if img:
            surface.blit(img, img.get_rect(center=cell_rect.center))
        else:
            draw_fallback_piece(surface, color, ptype, cell_rect.center)
        rects.append((cell_rect, ptype))
    return rects
 
 
# ---------------------------------------------------------------------------
# Game state
# ---------------------------------------------------------------------------
class GameState:
    def __init__(self):
        self.game = board()
        self.turn = "white"
        self.selected = None          # (row, col) of selected piece
        self.legal_targets = []       # safe legal moves for selection
        self.dragging = False
        self.drag_offset = (0, 0)
        self.last_move = None         # (start, end)
        self.flipped = False
        self.status = ""
        self.game_over = False
        self.promotion_pending = None  # (row, col) of pawn awaiting promotion
        self.flip_pending = False     # True while waiting out FLIP_DELAY_MS
        self.flip_at = 0              # pygame.time.get_ticks() value to flip at
        self.bot_color = None         # None = 2-player, otherwise "white"/"black" -- the color the bot plays
        self.bot_thinking = False     # True while a background thread is computing the bot's move
        self.bot_move_result = "pending"  # "pending" while thread runs, else the move tuple (or None)
        self.game_id = 0              # bumped on reset so stale bot threads don't apply moves to the wrong game
 
 
state = GameState()
 
 
def update_status():
    if state.game_over:
        return
    in_check = state.game.check(state.turn)
    has_move = color_has_any_move(state.game, state.turn)
    if not has_move:
        state.game_over = True
        if in_check:
            winner = "Black" if state.turn == "white" else "White"
            state.status = f"Checkmate — {winner} wins!"
        else:
            state.status = "Stalemate — draw."
    elif in_check:
        state.status = f"{state.turn.capitalize()} is in check"
    else:
        state.status = f"{state.turn.capitalize()} to move"
 
 
update_status()
 
 
def attempt_move(start, end):
    moving_piece = state.game.board[start[0]][start[1]]
    success = state.game.move_piece(start, end)
    if not success:
        return False
 
    state.last_move = (start, end)
 
    # Pawn promotion
    if isinstance(moving_piece, pawn) and end[0] in (0, 7):
        state.promotion_pending = end
    else:
        state.turn = "black" if state.turn == "white" else "white"
        state.flip_pending = True
        state.flip_at = pygame.time.get_ticks() + FLIP_DELAY_MS
        update_status()
        maybe_start_bot_turn()
 
    return True
 
 
def finish_promotion(chosen_type):
    row, col = state.promotion_pending
    piece_obj = state.game.board[row][col]
    piece_obj.promote(chosen_type)
    state.promotion_pending = None
    state.turn = "black" if state.turn == "white" else "white"
    state.flip_pending = True
    state.flip_at = pygame.time.get_ticks() + FLIP_DELAY_MS
    update_status()
    maybe_start_bot_turn()
 
 
def apply_bot_move(move):
    """Plays a (start, end) move returned by bot.bot(). Unlike attempt_move(),
    this always auto-promotes to queen since there's no UI to ask the bot
    for a promotion choice."""
    start, end = move
    moving_piece = state.game.board[start[0]][start[1]]
    success = state.game.move_piece(start, end)
    if not success:
        return False  # shouldn't happen -- bot.bot() only returns legal moves
 
    state.last_move = (start, end)
 
    if isinstance(moving_piece, pawn) and end[0] in (0, 7):
        moving_piece.promote("queen")
 
    state.turn = "black" if state.turn == "white" else "white"
    state.flip_pending = True
    state.flip_at = pygame.time.get_ticks() + FLIP_DELAY_MS
    update_status()
    return True
 
 
def maybe_start_bot_turn():
    """If it's currently the bot's turn, kicks off a background thread to
    compute its move so the window doesn't freeze while minimax runs."""
    if state.game_over or state.promotion_pending is not None:
        return
    if state.bot_color != state.turn or state.bot_thinking:
        return
 
    state.bot_thinking = True
    state.bot_move_result = "pending"
    grid_snapshot = [row[:] for row in state.game.board]
    color = state.turn
    game_id = state.game_id
 
    def worker():
        move = compute_bot_move(grid_snapshot, color, depth=BOT_DEPTH)
        if game_id == state.game_id:  # discard if a reset happened meanwhile
            state.bot_move_result = move
 
    threading.Thread(target=worker, daemon=True).start()
 
 
def set_bot_mode(bot_plays_color):
    state.bot_color = bot_plays_color
    reset_game()
 
 
def reset_game():
    state.game = board()
    state.turn = "white"
    state.selected = None
    state.legal_targets = []
    state.dragging = False
    state.last_move = None
    state.status = ""
    state.game_over = False
    state.promotion_pending = None
    state.flipped = False
    state.flip_pending = False
    state.bot_thinking = False
    state.bot_move_result = "pending"
    state.game_id += 1
    update_status()
    maybe_start_bot_turn()
 
 
# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------
def draw_board_squares():
    king_in_check_pos = None
    if not state.game_over and state.game.check(state.turn):
        king_in_check_pos = (
            state.game.white_king_position if state.turn == "white" else state.game.black_king_position
        )
 
    for row in range(8):
        for col in range(8):
            x, y = board_to_screen(row, col, state.flipped)
            base_color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
            pygame.draw.rect(screen, base_color, (x, y, SQUARE_SIZE, SQUARE_SIZE))
 
            if state.last_move and (row, col) in state.last_move:
                overlay = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                overlay.fill((*LAST_MOVE_COLOR, 110))
                screen.blit(overlay, (x, y))
 
            if state.selected == (row, col):
                overlay = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                overlay.fill((*SELECT_COLOR, 140))
                screen.blit(overlay, (x, y))
 
            if king_in_check_pos == (row, col):
                overlay = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                overlay.fill((*CHECK_COLOR, 130))
                screen.blit(overlay, (x, y))
 
 
def draw_move_hints():
    for (row, col) in state.legal_targets:
        x, y = board_to_screen(row, col, state.flipped)
        center = (x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2)
        target_piece = state.game.board[row][col]
        if target_piece != "":
            pygame.draw.circle(screen, CAPTURE_RING_COLOR, center, SQUARE_SIZE // 2 - 4, 4)
        else:
            pygame.draw.circle(screen, MOVE_DOT_COLOR, center, 10)
 
 
def draw_pieces(mouse_pos):
    for row in range(8):
        for col in range(8):
            if state.dragging and state.selected == (row, col):
                continue  # drawn separately, under the cursor
            piece_obj = state.game.board[row][col]
            if piece_obj == "":
                continue
            x, y = board_to_screen(row, col, state.flipped)
            draw_piece(screen, piece_obj, (x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2))
 
    if state.dragging and state.selected:
        piece_obj = state.game.board[state.selected[0]][state.selected[1]]
        if piece_obj != "":
            draw_piece(screen, piece_obj, mouse_pos)
 
 
def draw_side_panel():
    pygame.draw.rect(screen, PANEL_BG, (BOARD_PIXELS, 0, SIDE_PANEL_WIDTH, WINDOW_HEIGHT))
    flip_button.draw(screen)
    reset_button.draw(screen)
    play_white_button.draw(screen)
    play_black_button.draw(screen)
 
    if state.bot_color is None:
        mode_text = "Mode: 2 Player"
    else:
        human_color = "Black" if state.bot_color == "white" else "White"
        mode_text = f"Mode: You are {human_color}"
    mode_surface = FONT_SMALL.render(mode_text, True, (170, 170, 170))
    screen.blit(mode_surface, (BOARD_PIXELS + 20, 245))
 
    y = 275
    if state.bot_thinking:
        thinking_surface = FONT_SMALL.render("Bot is thinking...", True, (220, 190, 90))
        screen.blit(thinking_surface, (BOARD_PIXELS + 20, y))
        y += 22
 
    status_lines = wrap_text(state.status, FONT, SIDE_PANEL_WIDTH - 40)
    for line in status_lines:
        text = FONT.render(line, True, TEXT_COLOR)
        screen.blit(text, (BOARD_PIXELS + 20, y))
        y += 28
 
    turn_swatch_color = (250, 250, 250) if state.turn == "white" else (30, 30, 30)
    if not state.game_over:
        pygame.draw.circle(screen, turn_swatch_color, (BOARD_PIXELS + 30, y + 15), 10)
        pygame.draw.circle(screen, (150, 150, 150), (BOARD_PIXELS + 30, y + 15), 10, 1)
 
    move_no_text = FONT_SMALL.render(f"Move: {state.game.turn_number}", True, (170, 170, 170))
    screen.blit(move_no_text, (BOARD_PIXELS + 20, y + 40))
 
    draw_move_history(screen, top=y + 70)
 
 
def pos_to_algebraic(pos):
    """(row, col) -> algebraic square name, e.g. (6, 4) -> 'e2'."""
    row, col = pos
    file_letter = chr(ord('a') + col)
    rank_number = 8 - row
    return f"{file_letter}{rank_number}"
 
 
def draw_move_history(surface, top):
    """Renders the move list (e.g. '1. e2e4  e7e5') in the side panel,
    scrolled to always show the most recent moves."""
    x = BOARD_PIXELS + 20
    y = top
    bottom_limit = WINDOW_HEIGHT - 50
    line_height = 20
 
    header = FONT_SMALL.render("Moves", True, (170, 170, 170))
    surface.blit(header, (x, y))
    y += line_height
 
    history = state.game.turn_history
    max_visible_pairs = (bottom_limit - y) // line_height
    total_pairs = (len(history) + 1) // 2
    start_pair = max(0, total_pairs - max_visible_pairs)
 
    for pair_index in range(start_pair, total_pairs):
        white_i = pair_index * 2
        black_i = white_i + 1
        white_move = pos_to_algebraic(history[white_i][0]) + pos_to_algebraic(history[white_i][1])
        line = f"{pair_index + 1}. {white_move}"
        if black_i < len(history):
            black_move = pos_to_algebraic(history[black_i][0]) + pos_to_algebraic(history[black_i][1])
            line += f"  {black_move}"
        text = FONT_SMALL.render(line, True, TEXT_COLOR)
        surface.blit(text, (x, y))
        y += line_height
 
 
def wrap_text(text, font, max_width):
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]
