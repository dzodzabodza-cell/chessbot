from game import *

def get_pawns(board, color):
    pawns = []
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece != "" and piece.color == color and piece.type == "pawn":
                pawns.append((row, col))
    return pawns

def pawn_structure_score(board, color):
    pawns = get_pawns(board, color)
    score = 0

    # Check for doubled pawns
    for col in range(8):
        count = sum(1 for row in range(8) if board[row][col] != "" and board[row][col].color == color and board[row][col].type == "pawn")
        if count > 1:
            score -= (count - 1) * 0.5  # Penalize for each additional pawn in the same file

    # Check for isolated pawns
    for row, col in pawns:
        isolated = True
        if col > 0 and any(board[r][col - 1] != "" and board[r][col - 1].color == color and board[r][col - 1].type == "pawn" for r in range(8)):
            isolated = False
        if col < 7 and any(board[r][col + 1] != "" and board[r][col + 1].color == color and board[r][col + 1].type == "pawn" for r in range(8)):
            isolated = False
        if isolated:
            score -= 0.5  # Penalize for isolated pawn

    return score

def find_king_position(board, color):
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece != "" and piece.color == color and piece.type == "king":
                return (row, col)
    return None

def king_safety_score(board, color):
    king_position = find_king_position(board, color)
    if king_position is None:
        return 0 
    row, col = king_position
    safety_score = 0

    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for dr, dc in directions:
        r, c = row + dr, col + dc
        if 0 <= r < 8 and 0 <= c < 8:
            if board[r][c] != "" and board[r][c].color == color:
                safety_score += 1

    return safety_score

def grid_in_check(board, color):
    king_position = find_king_position(board, color)
    if king_position is None:
        return False 
    row, col = find_king_position(board, color)
    opponent_color = "black" if color == "white" else "white"
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece != "" and piece.color == opponent_color:
                legal_moves = piece.get_legal_moves((r, c), board)
                if (row, col) in legal_moves:
                    return True  # King is in check

    return False

def mobility_score(board, color):
    mobility = 0
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece != "" and piece.color == color:
                legal_moves = piece.get_legal_moves((row, col), board)
                safe_moves = []
                for move in legal_moves:
                    new_board = [r.copy() for r in board]
                    new_board[move[0]][move[1]] = piece
                    new_board[row][col] = ""
                    if not grid_in_check(new_board, color):
                        safe_moves.append(move)
                mobility += len(safe_moves)
    return mobility

def bishop_squares(board, color):
    bishop_squares = 0
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece != "" and piece.color == color and piece.type == "bishop":
                legal_moves = piece.get_legal_moves((row, col), board)
                safe_moves = []
                for move in legal_moves:
                    new_board = [r.copy() for r in board]
                    new_board[move[0]][move[1]] = piece
                    new_board[row][col] = ""
                    if not grid_in_check(new_board, color):
                        safe_moves.append(move)
                bishop_squares += len(safe_moves)
    return bishop_squares

def rook_squares(board, color):
    rook_squares = 0
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece != "" and piece.color == color and piece.type == "rook":
                legal_moves = piece.get_legal_moves((row, col), board)
                safe_moves = []
                for move in legal_moves:
                    new_board = [r.copy() for r in board]
                    new_board[move[0]][move[1]] = piece
                    new_board[row][col] = ""
                    if not grid_in_check(new_board, color):
                        safe_moves.append(move)
                rook_squares += len(safe_moves)
    return rook_squares

def material_count(board):
    white_material = 0
    black_material = 0

    for row in board:
        for piece in row:
            if piece != "":
                if piece.color == "white":
                    white_material += piece.value
                else:
                    black_material += piece.value

    return white_material, black_material

def evaluate_board(board):
    white_material, black_material = material_count(board)
    material_score = white_material - black_material

    white_pawn_structure = pawn_structure_score(board, "white")
    black_pawn_structure = pawn_structure_score(board, "black")
    pawn_structure_score_total = white_pawn_structure - black_pawn_structure

    white_king_safety = king_safety_score(board, "white")
    black_king_safety = king_safety_score(board, "black")
    king_safety_score_total = white_king_safety - black_king_safety

    white_mobility = mobility_score(board, "white")
    black_mobility = mobility_score(board, "black")
    mobility_score_total = white_mobility - black_mobility

    white_bishop_squares = bishop_squares(board, "white")
    black_bishop_squares = bishop_squares(board, "black")
    bishop_squares_total = white_bishop_squares - black_bishop_squares

    white_rook_squares = rook_squares(board, "white")
    black_rook_squares = rook_squares(board, "black")
    rook_squares_total = white_rook_squares - black_rook_squares

    # Combine all scores with weights
    total_score = (material_score * 1.0 +
                   pawn_structure_score_total * 0.5 +
                   king_safety_score_total * 0.3 +
                   mobility_score_total * 0.2 +
                   bishop_squares_total * 0.1 +
                   rook_squares_total * 0.1)

    return total_score