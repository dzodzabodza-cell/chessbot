from game import *
from representation import *
from bot import bot
import pygame

def main():
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
 
        if state.flip_pending and pygame.time.get_ticks() >= state.flip_at:
            state.flipped = not state.flipped
            state.flip_pending = False
 
        if state.bot_thinking and state.bot_move_result != "pending":
            move = state.bot_move_result
            state.bot_thinking = False
            state.bot_move_result = "pending"
            if move is not None:
                apply_bot_move(move)
 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
 
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if flip_button.clicked(event.pos):
                    state.flipped = not state.flipped
                    continue
                if reset_button.clicked(event.pos):
                    reset_game()
                    continue
                if play_white_button.clicked(event.pos):
                    set_bot_mode("black")  # human plays white, bot plays black
                    continue
                if play_black_button.clicked(event.pos):
                    set_bot_mode("white")  # human plays black, bot plays white
                    continue
 
                if state.promotion_pending:
                    rects = draw_promotion_menu(screen, state.turn, state.flipped, state.promotion_pending)
                    for rect, ptype in rects:
                        if rect.collidepoint(event.pos):
                            finish_promotion(ptype)
                            break
                    continue
 
                if state.game_over or state.bot_thinking:
                    continue
 
                square = screen_to_board(*event.pos, state.flipped)
                if square is None:
                    continue
                row, col = square
                piece_obj = state.game.board[row][col]
 
                if state.selected is None:
                    if piece_obj != "" and piece_obj.color == state.turn:
                        state.selected = (row, col)
                        state.legal_targets = get_safe_legal_moves(state.game, row, col)
                        state.dragging = True
                else:
                    if square == state.selected:
                        state.dragging = True
                    elif square in state.legal_targets:
                        attempt_move(state.selected, square)
                        state.selected = None
                        state.legal_targets = []
                        state.dragging = False
                    elif piece_obj != "" and piece_obj.color == state.turn:
                        state.selected = (row, col)
                        state.legal_targets = get_safe_legal_moves(state.game, row, col)
                        state.dragging = True
                    else:
                        state.selected = None
                        state.legal_targets = []
                        state.dragging = False
 
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if not state.dragging or state.selected is None:
                    continue
                square = screen_to_board(*event.pos, state.flipped)
                state.dragging = False
                if square and square in state.legal_targets:
                    attempt_move(state.selected, square)
                    state.selected = None
                    state.legal_targets = []
                # if released on an invalid square, keep the piece selected
                # so the player can click a valid destination instead
 
        screen.fill((0, 0, 0))
        draw_board_squares()
        draw_move_hints()
        draw_pieces(mouse_pos)
        draw_side_panel()
        if state.promotion_pending:
            draw_promotion_menu(screen, state.turn, state.flipped, state.promotion_pending)
        pygame.display.flip()
        clock.tick(60)
 
    pygame.quit()
    sys.exit()
 
 
if __name__ == "__main__":
    main()
