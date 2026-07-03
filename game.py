
class piece:
    def __init__(self, color, type):
        self.color = color
        self.type = type
        self.has_moved = False
        self.value = None

class pawn(piece):
    def __init__(self, color):
        super().__init__(color, 'pawn')
        self.value = 1
    
    def get_legal_moves(self, position, board):
        moves = []
        row, col = position
        direction = -1 if self.color == 'white' else 1

        if board[row + direction][col] == '':
            moves.append((row + direction, col))
            if (self.color == 'white' and row == 6) or (self.color == 'black' and row == 1):
                if board[row + 2 * direction][col] == '':
                    moves.append((row + 2 * direction, col))

        for dc in [-1, 1]:
            new_col = col + dc
            if 0 <= new_col < 8:
                target_piece = board[row + direction][new_col]
                if target_piece != '' and target_piece.color != self.color:
                    moves.append((row + direction, new_col))

        return moves
    
    def promote(self, new_type):
        if new_type in ['queen', 'rook', 'bishop', 'knight']:
            self.type = new_type
        else:
            raise ValueError("Invalid promotion type. Choose from 'queen', 'rook', 'bishop', or 'knight'.")
    

class knight(piece):
    def __init__(self, color):
        super().__init__(color, 'knight')
        self.value = 3
    
    def get_legal_moves(self, position, board):
        moves = []
        row, col = position
        knight_moves = [
            (row + 2, col + 1), (row + 2, col - 1),
            (row - 2, col + 1), (row - 2, col - 1),
            (row + 1, col + 2), (row + 1, col - 2),
        ]
        for move in knight_moves:
            r, c = move
            if 0 <= r < 8 and 0 <= c < 8:
                target_piece = board[r][c]
                if target_piece == '' or target_piece.color != self.color:
                    moves.append((r, c))
        return moves

class bishop(piece):
    def __init__(self, color):
        super().__init__(color, 'bishop')
        self.value = 3
    
    def get_legal_moves(self, position, board):
        moves = []
        row, col = position
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                if board[r][c] == '':
                    moves.append((r, c))
                else:
                    if board[r][c].color != self.color:
                        moves.append((r, c))
                    break
                r += dr
                c += dc
        return moves

class rook(piece):
    def __init__(self, color):
        super().__init__(color, 'rook')
        self.value = 5
    
    def get_legal_moves(self, position, board):
        moves = []
        row, col = position
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                if board[r][c] == '':
                    moves.append((r, c))
                else:
                    if board[r][c].color != self.color:
                        moves.append((r, c))
                    break
                r += dr
                c += dc
        return moves

class queen(piece):
    def __init__(self, color):
        super().__init__(color, 'queen')
        self.value = 9
    
    def get_legal_moves(self, position, board):
        moves = []
        row, col = position
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                if board[r][c] == '':
                    moves.append((r, c))
                else:
                    if board[r][c].color != self.color:
                        moves.append((r, c))
                    break
                r += dr
                c += dc
        return moves

class king(piece):
    def __init__(self, color):
        super().__init__(color, 'king')
        self.value = 0
    
    def get_legal_moves(self, position, board):
        moves = []
        row, col = position
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                if board[r][c] == '':
                    moves.append((r, c))
                else:
                    if board[r][c].color != self.color:
                        moves.append((r, c))
        return moves


class board:

    def __init__(self):
        self.board = [['' for _ in range(8)] for _ in range(8)]
        self.board[0] = [rook('black'), knight('black'), bishop('black'), queen('black'), king('black'), bishop('black'), knight('black'), rook('black')]
        self.board[1] = [pawn('black') for _ in range(8)]
        self.turn_history = []
        self.turn_number = 0
        self.white_king_position = (7, 4)
        self.black_king_position = (0, 4)
        for row in range(2, 6):
            self.board[row] = ['' for _ in range(8)]
        self.board[6] = [pawn('white') for _ in range(8)]
        self.board[7] = [rook('white'), knight('white'), bishop('white'), queen('white'), king('white'), bishop('white'), knight('white'), rook('white')]

    def check(self, color):
        king_position = self.white_king_position if color == 'white' else self.black_king_position
        return self._check_grid(self.board, king_position, color)
 
    def _check_grid(self, grid, king_position, color):
        for row in range(8):
            for col in range(8):
                piece = grid[row][col]
                if piece != '' and piece.color != color:
                    if king_position in piece.get_legal_moves((row, col), grid):
                        return True
        return False
    
    def king_castle(self, color):
        king_row = 7 if color == 'white' else 0
        king_pos = self.white_king_position if color == 'white' else self.black_king_position
        if king_pos != (king_row, 4):
            return False
        king_piece = self.board[king_row][4]
        if not isinstance(king_piece, king) or king_piece.has_moved:
            return False
        if self.board[king_row][5] != '' or self.board[king_row][6] != '':
            return False
        rook_piece = self.board[king_row][7]
        if not isinstance(rook_piece, rook) or rook_piece.has_moved:
            return False
        if (self._check_grid(self.board, (king_row, 4), color)
                or self._check_grid(self.board, (king_row, 5), color)
                or self._check_grid(self.board, (king_row, 6), color)):
            return False
        return True

    def queen_castle(self, color):
            king_row = 7 if color == 'white' else 0
            king_pos = self.white_king_position if color == 'white' else self.black_king_position
            if king_pos != (king_row, 4):
                return False
            king_piece = self.board[king_row][4]
            if not isinstance(king_piece, king) or king_piece.has_moved:
                return False
            if self.board[king_row][1] != '' or self.board[king_row][2] != '' or self.board[king_row][3] != '':
                return False
            rook_piece = self.board[king_row][0]
            if not isinstance(rook_piece, rook) or rook_piece.has_moved:
                return False
            if (self._check_grid(self.board, (king_row, 4), color)
                    or self._check_grid(self.board, (king_row, 3), color)
                    or self._check_grid(self.board, (king_row, 2), color)):
                return False
            return True

    def king_castle_move(self, color):
        king_row = 7 if color == 'white' else 0
        king_piece = self.board[king_row][4]
        rook_piece = self.board[king_row][7]
        self.board[king_row][6] = king_piece
        self.board[king_row][4] = ''
        self.board[king_row][5] = rook_piece
        self.board[king_row][7] = ''
        king_piece.has_moved = True
        rook_piece.has_moved = True
        if color == 'white':
            self.white_king_position = (king_row, 6)
        else:
            self.black_king_position = (king_row, 6)

    
    def queen_castle_move(self, color):
        king_row = 7 if color == 'white' else 0
        king_piece = self.board[king_row][4]
        rook_piece = self.board[king_row][0]
        self.board[king_row][2] = king_piece
        self.board[king_row][4] = ''
        self.board[king_row][3] = rook_piece
        self.board[king_row][0] = ''
        king_piece.has_moved = True
        rook_piece.has_moved = True
        if color == 'white':
            self.white_king_position = (king_row, 2)
        else:
            self.black_king_position = (king_row, 2)

    def _has_escape(self, color):
        king_position = self.white_king_position if color == 'white' else self.black_king_position
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != '' and piece.color == color:
                    legal_moves = piece.get_legal_moves((row, col), self.board)
                    for move in legal_moves:
                        new_board = [r.copy() for r in self.board]
                        new_board[move[0]][move[1]] = piece
                        new_board[row][col] = ''
                        new_king_position = move if isinstance(piece, king) else king_position
                        if not self._check_grid(new_board, new_king_position, color):
                            return True
        return False
    
    def checkmate(self, color):
            if not self.check(color):
                return False
            return not self._has_escape(color)
    
    def stalemate(self, color):
            if self.check(color):
                return False
            return not self._has_escape(color)
        
    def en_passant(self, start_pos, end_pos):
            piece = self.board[start_pos[0]][start_pos[1]]
            if not isinstance(piece, pawn):
                return False
            if abs(start_pos[0] - end_pos[0]) != 1 or abs(start_pos[1] - end_pos[1]) != 1:
                return False
            target_piece = self.board[start_pos[0]][end_pos[1]]
            if not isinstance(target_piece, pawn) or target_piece.color == piece.color:
                return False
            if (piece.color == 'white' and start_pos[0] != 3) or (piece.color == 'black' and start_pos[0] != 4):
                return False
            if len(self.turn_history) < 1:
                return False
            last_move = self.turn_history[-1]
            if last_move[0][0] != (6 if piece.color == 'white' else 1) or last_move[1][0] != (4 if piece.color == 'white' else 3):
                return False
            return True
    
    def move_piece(self, start_pos, end_pos):
        piece = self.board[start_pos[0]][start_pos[1]]
        if piece == '':
            return False
        legal_moves = piece.get_legal_moves(start_pos, self.board)
        if isinstance(piece, king):
            king_row = 7 if piece.color == 'white' else 0
            if start_pos == (king_row, 4) and end_pos == (king_row, 6) and self.king_castle(piece.color):
                self.king_castle_move(piece.color)
                self.turn_history.append((start_pos, end_pos, piece.color))
                self.turn_number += 1
                return True
            if start_pos == (king_row, 4) and end_pos == (king_row, 2) and self.queen_castle(piece.color):
                self.queen_castle_move(piece.color)
                self.turn_history.append((start_pos, end_pos, piece.color))
                self.turn_number += 1
                return True

        if end_pos not in legal_moves:
            return False
        self.board[end_pos[0]][end_pos[1]] = piece
        self.board[start_pos[0]][start_pos[1]] = ''
        if isinstance(piece, king):
            if piece.color == 'white':
                self.white_king_position = end_pos
            else:
                self.black_king_position = end_pos
        if isinstance(piece, pawn) and self.en_passant(start_pos, end_pos):
            self.board[start_pos[0]][end_pos[1]] = ''
        self.board[end_pos[0]][end_pos[1]].has_moved = True
        self.turn_history.append((start_pos, end_pos, piece.color))
        self.turn_number += 1
        if self.check(piece.color):
            self.board[start_pos[0]][start_pos[1]] = piece
            self.board[end_pos[0]][end_pos[1]] = ''
            if isinstance(piece, king):
                if piece.color == 'white':
                    self.white_king_position = start_pos
                else:
                    self.black_king_position = start_pos
            return False
        return True
    
    def stalemate(self, color):
        if self.check(color):
            return False
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != '' and piece.color == color:
                    legal_moves = piece.get_legal_moves((row, col), self.board)
                    for move in legal_moves:
                        new_board = [r.copy() for r in self.board]
                        new_board[move[0]][move[1]] = piece
                        new_board[row][col] = ''
                        if not new_board.check(color):
                            return False
        return True