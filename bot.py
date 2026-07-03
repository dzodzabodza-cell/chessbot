from game import *
from evaluate import *

def minimax(board, depth, maximizing_player, color):
    if depth == 0:
        return evaluate_board(board)

    if maximizing_player:
        max_eval = float('-inf')
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece != "" and piece.color == color:
                    legal_moves = piece.get_legal_moves((row, col), board)
                    for move in legal_moves:
                        new_board = [r.copy() for r in board]
                        new_board[move[0]][move[1]] = piece
                        new_board[row][col] = ""
                        eval = minimax(new_board, depth - 1, False, color)
                        max_eval = max(max_eval, eval)
        return max_eval
    else:
        min_eval = float('inf')
        opponent_color = "black" if color == "white" else "white"
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece != "" and piece.color == opponent_color:
                    legal_moves = piece.get_legal_moves((row, col), board)
                    for move in legal_moves:
                        new_board = [r.copy() for r in board]
                        new_board[move[0]][move[1]] = piece
                        new_board[row][col] = ""
                        eval = minimax(new_board, depth - 1, True, color)
                        min_eval = min(min_eval, eval)
        return min_eval

def bot(board, color, depth=2):
    best_move = None
    best_score = float('-inf') if color == "white" else float('inf')
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece != "" and piece.color == color:
                legal_moves = piece.get_legal_moves((row, col), board)
                for move in legal_moves:
                    new_board = [r.copy() for r in board]
                    new_board[move[0]][move[1]] = piece
                    new_board[row][col] = ""
                    score = minimax(new_board, depth - 1, color == "black", color)
                    if (color == "white" and score > best_score) or (color == "black" and score < best_score):
                        best_score = score
                        best_move = ((row, col), move)
    return best_move