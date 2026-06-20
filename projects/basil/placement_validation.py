# Portfolio excerpt, adapted. From a CLI crossword generator.
# Placement is legal only when the word stays in bounds, every overlap is the
# same letter, and it neither fuses with a parallel word nor abuts one at an end.


class GridValidator:
    def __init__(self, grid):
        self.grid = grid
        self.height = len(grid)
        self.width = len(grid[0]) if grid else 0

    def is_valid_placement(self, word, row, col, direction):
        if row < 0 or col < 0:
            return False
        if direction == 'H':
            if col + len(word) > self.width:
                return False
        else:
            if row + len(word) > self.height:
                return False

        for i, char in enumerate(word):
            r = row if direction == 'H' else row + i
            c = col + i if direction == 'H' else col

            # an occupied cell is fine only if it already holds this letter (an
            # intersection); any other letter is a conflict
            if self.grid[r][c] != ' ' and self.grid[r][c] != char:
                return False

            is_intersection = self.grid[r][c] == char
            if is_intersection:
                continue

            # writing into an empty cell that touches a perpendicular word would
            # glue the two together, so reject any neighbour on that axis
            if direction == 'H':
                if (r > 0 and self.grid[r - 1][c] != ' ') or \
                   (r < self.height - 1 and self.grid[r + 1][c] != ' '):
                    return False
            else:
                if (c > 0 and self.grid[r][c - 1] != ' ') or \
                   (c < self.width - 1 and self.grid[r][c + 1] != ' '):
                    return False

        # the cell just before the start and just after the end must be clear,
        # otherwise this word runs straight into another and they read as one
        if direction == 'H':
            if col > 0 and self.grid[row][col - 1] != ' ':
                return False
            end = col + len(word)
            if end < self.width and self.grid[row][end] != ' ':
                return False
        else:
            if row > 0 and self.grid[row - 1][col] != ' ':
                return False
            end = row + len(word)
            if end < self.height and self.grid[end][col] != ' ':
                return False

        return True


if __name__ == '__main__':
    grid = [[' '] * 6 for _ in range(6)]
    for i, ch in enumerate('PYTHON'):
        grid[0][i] = ch
    v = GridValidator(grid)
    print('crosses at the H:', v.is_valid_placement('HASH', 0, 3, 'V'))  # True
    print('would fuse:', v.is_valid_placement('CODE', 1, 0, 'H'))        # False
