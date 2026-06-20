# Portfolio excerpt, adapted. From a CLI crossword generator.
# Finds every legal spot where a new word can cross an already-placed one.

# A placed word is {'word', 'row', 'col', 'dir'}, dir in {'H', 'V'}.


class CrosswordPlacer:
    def __init__(self, width=20, height=20):
        self.width = width
        self.height = height
        self.grid = [[' ' for _ in range(width)] for _ in range(height)]

    def find_possible_intersections(self, word, placed_list):
        """Return (row, col, dir) placements where word crosses an already-placed word."""
        placements = []

        for placed in placed_list:
            placed_word = placed['word']

            for char_idx, char in enumerate(word):
                for p_char_idx, p_char in enumerate(placed_word):
                    if char != p_char:
                        continue

                    # crossing word runs perpendicular to the one it crosses
                    new_dir = 'V' if placed['dir'] == 'H' else 'H'

                    if new_dir == 'V':
                        # match column is fixed by the placed word; back off
                        # char_idx rows so the new word's matching cell lands there
                        row = placed['row'] - char_idx
                        col = placed['col'] + p_char_idx
                    else:  # new_dir == 'H'
                        row = placed['row'] + p_char_idx
                        col = placed['col'] - char_idx

                    if self.is_valid_placement(word, row, col, new_dir):
                        placements.append((row, col, new_dir))

        return placements

    def is_valid_placement(self, word, row, col, direction):
        """Return True if word fits the grid bounds at (row, col); conflict and adjacency checks live in placement_validation.py."""
        if row < 0 or col < 0:
            return False
        if direction == 'H':
            return col + len(word) <= self.width
        return row + len(word) <= self.height


if __name__ == '__main__':
    placer = CrosswordPlacer(width=12, height=12)
    placed = [{'word': 'PYTHON', 'row': 5, 'col': 3, 'dir': 'H'}]
    # HASH shares H with PYTHON; TONE shares T, O, N
    for cand in ('HASH', 'TONE'):
        spots = placer.find_possible_intersections(cand, placed)
        print(cand, '->', spots)
