#!/usr/bin/env python3
from hongwu import Player, combo_type, card_power

# Create a test player with a hand that has various options
test_player = Player(0, is_human=False)
test_player.hand = ["3C", "4C", "5C", "8C", "9C", "AC", "2C", "5H"]

print("Test player hand:", test_player.hand)
print()

# Get all legal moves when starting (prev=None)
moves = test_player.legal_moves(None)

# Remove duplicates while preserving order
unique_moves = []
seen = set()
for move in moves:
    move_tuple = tuple(sorted(move))
    if move_tuple not in seen:
        seen.add(move_tuple)
        unique_moves.append(move)

print("All legal moves when starting:")
for i, move in enumerate(unique_moves):
    print(f"  {i+1}. {move} ({combo_type(move)}) - length: {len(move)}")

print()

# Test the AI's choice
ai_choice = test_player.choose_play(None)
print(f"AI chose: {ai_choice} ({combo_type(ai_choice)})")

# Let's also test the sorting logic manually
print("\nTesting sorting logic:")
sorted_moves = sorted(unique_moves, key=lambda m: (
    combo_type(m) != 'bomb',  # Bombs first
    combo_type(m) == 'single',  # Singles last (False sorts before True)
    -len(m),  # Longer combinations preferred (negative for reverse sort)
    card_power(max(m, key=card_power))  # Lower power preferred
))

print("Sorted moves (best to worst):")
for i, move in enumerate(sorted_moves):
    print(f"  {i+1}. {move} ({combo_type(move)}) - length: {len(move)}")

print(f"\nBest move according to sorting: {sorted_moves[0]}")
print(f"AI chose: {ai_choice}")
print(f"AI choice matches best move: {ai_choice == sorted_moves[0]}") 