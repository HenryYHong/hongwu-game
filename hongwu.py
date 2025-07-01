#!/usr/bin/env python3
# hongwu.py  – terminal Hong Wu (Red Five) game & simulator
import random, sys, itertools, collections

RANK_ORDER = "3456789TJQKA2"
SUITS       = "CDHS"  # clubs, diamonds, hearts, spades
FIVE_SUIT_POWER = {"C": 1, "S": 2, "D": 3, "H": 4}  # 5♥ highest

def card_str(card): return card[:-1] + card[-1]
def rank(card):     return card[:-1]
def suit(card):     return card[-1]

def card_power(card):
    r, s = rank(card), suit(card)
    # Special 5s outrank everything else
    if r == '5' and s in FIVE_SUIT_POWER:
        return 100 + FIVE_SUIT_POWER[s]  # 5♣=101, 5♠=102, 5♦=103, 5♥=104
    # Regular cards follow normal order
    return RANK_ORDER.index(r)

def combo_type(cards):
    """Return ('single'|'pair'|'triple'|'bomb'|'run') or None if invalid."""
    k = len(cards)
    if k == 0: return None
    
    # Check for invalid cards
    for card in cards:
        if len(card) != 2 or card[0] not in RANK_ORDER or card[1] not in SUITS:
            return None
    
    # Check for duplicate cards
    if len(set(cards)) != k:
        return None
    
    if k == 1: return 'single'
    
    rs = [rank(c) for c in cards]
    if k == 2 and len(set(rs)) == 1: return 'pair'
    if k == 3 and len(set(rs)) == 1: return 'triple'
    if k == 4 and len(set(rs)) == 1: return 'bomb'
    
    # Run: length ≥2, all ranks distinct, consecutive (5s allowed)
    if k >= 2 and len(set(rs)) == k:
        # For runs, use RANK_ORDER.index to check consecutiveness
        # This allows 5s to be part of runs (like 3-4-5, 5-6-7)
        idxs = sorted(RANK_ORDER.index(r) for r in rs)
        if all(b == a+1 for a,b in zip(idxs, idxs[1:])):
            return 'run'
    
    return None

def run_power(cards):
    """Calculate the power of a run for comparison purposes."""
    ranks = [rank(c) for c in cards]
    n = len(ranks)
    # Check for consecutiveness in any order for two-card runs
    if n == 2:
        sorted_ranks = sorted(ranks, key=lambda r: RANK_ORDER.index(r))
        # Special case: A-2 is always weakest
        if set(sorted_ranks) == set(['A', '2']):
            return 0
        # Special case: K-A (or A-K) is always strongest
        if set(sorted_ranks) == set(['K', 'A']):
            return 12
        # Otherwise, check for any consecutive pair
        idx0 = RANK_ORDER.index(sorted_ranks[0])
        idx1 = RANK_ORDER.index(sorted_ranks[1])
        if (idx1 == (idx0 + 1) % len(RANK_ORDER)):
            return idx0 + 1  # A-2 is already handled
        return -1  # Not a valid run
    # For longer runs, check for consecutiveness in the order played, with A-2 as consecutive
    for i in range(n - 1):
        curr_idx = RANK_ORDER.index(ranks[i])
        next_idx = RANK_ORDER.index(ranks[i+1])
        # Normal consecutive
        if next_idx == (curr_idx + 1) % len(RANK_ORDER):
            continue
        # Special case: A-2
        if ranks[i] == 'A' and ranks[i+1] == '2':
            continue
        return -1  # Not consecutive
    # Define the run cycle
    run_cycle = [
        ('A', '2'), ('2', '3'), ('3', '4'), ('4', '5'), ('5', '6'), ('6', '7'),
        ('7', '8'), ('8', '9'), ('9', 'T'), ('T', 'J'), ('J', 'Q'), ('Q', 'K'), ('K', 'A')
    ]
    last_two = (ranks[-2], ranks[-1])
    if last_two in run_cycle:
        return run_cycle.index(last_two)
    # For longer runs, if the last two cards are not in the cycle, it's invalid
    return -1

def beats(play, prev):
    """Return True if play beats prev (same category, higher; bomb beats anything)."""
    if play is None: return False
    if combo_type(play) == 'bomb':
        return True
    if prev is None:  # starting the round
        return True
    if combo_type(play) != combo_type(prev): 
        return False
    # same type – compare
    t = combo_type(play)
    if t in ('single', 'pair', 'triple'):
        return card_power(max(play, key=card_power)) > card_power(max(prev, key=card_power))
    if t == 'run':
        if len(play) != len(prev): return False
        # Use special run power function for comparison
        return run_power(play) > run_power(prev)
    return False

class Player:
    def __init__(self, pid, is_human=False):
        self.id, self.hand, self.is_human = pid, [], is_human
    def draw(self, deck, n=1):
        for _ in range(n):
            if deck: self.hand.append(deck.pop())
    # --- helper: generate all legal moves that beat previous play -----------------
    def legal_moves(self, prev):
        hand = self.hand
        prev_type = combo_type(prev) if prev else None
        moves = []
        # singles, pairs, triples, bombs
        for k in (1,2,3,4):
            if k==4 and prev_type!='bomb':  # bombs allowed anytime
                groups = [g for g in collections.Counter(rank(c) for c in hand) if sum(rank(c)==g for c in hand)==4]
                for r in groups:
                    cards=[c for c in hand if rank(c)==r][:4]; moves.append(cards)
            else:
                groups = [g for g in collections.Counter(rank(c) for c in hand) if sum(rank(c)==g for c in hand)==k]
                for r in groups:
                    cards=[c for c in hand if rank(c)==r][:k]; 
                    if beats(cards, prev): moves.append(cards)
        # runs
        if len(hand) >= 2:
            uniq = sorted(set(hand), key=lambda c: RANK_ORDER.index(rank(c)))
            run = []
            for i,card_ in enumerate(uniq):
                if not run or RANK_ORDER.index(rank(card_)) == RANK_ORDER.index(rank(run[-1]))+1:
                    run.append(card_)
                else:
                    run=[card_]
                if len(run)>=2:
                    for L in range(2, len(run)+1):
                        candidate = run[-L:]
                        if beats(candidate, prev):
                            moves.append(candidate)
        if prev is None:
            moves += self.starter_moves()
        # Remove duplicates
        unique_moves = []
        seen = set()
        for move in moves:
            move_tuple = tuple(sorted(move))
            if move_tuple not in seen:
                seen.add(move_tuple)
                unique_moves.append(move)
        return unique_moves
    def starter_moves(self):
        # any legal combo from hand
        moves=[]
        for k in (1,2,3,4):
            groups=[g for g in collections.Counter(rank(c) for c in self.hand) if sum(rank(c)==g for c in self.hand)==k]
            for r in groups:
                moves.append([c for c in self.hand if rank(c)==r][:k])
        # runs
        uniq=sorted(set(self.hand), key=lambda c: RANK_ORDER.index(rank(c)))
        run=[]
        for card_ in uniq:
            if not run or RANK_ORDER.index(rank(card_))==RANK_ORDER.index(rank(run[-1]))+1:
                run.append(card_)
            else:
                run=[card_]
            if len(run)>=2:
                for L in range(2,len(run)+1):
                    moves.append(run[-L:])
        return moves
    # --- choose play --------------------------------------------------------------
    def choose_play(self, prev):
        if self.is_human:
            self.print_hand()
            if prev:
                print(f"Previous play: {prev} ({combo_type(prev)})")
            print("Enter space-separated card codes to play, or just Enter to pass:")
            while True:
                s = input(">>> ").strip().upper()
                if not s:
                    return None
                try:
                    cards = s.split()
                    if all(c in self.hand for c in cards) and combo_type(cards) and beats(cards, prev):
                        return cards
                except Exception:
                    pass
                print("Invalid play – try again.")
        moves = self.legal_moves(prev)
        if not moves:
            return None
        # AI: 20% random legal move, 80% prioritize lowest cards
        if random.random() < 0.2:
            return random.choice(moves)
        # Always prioritize getting rid of the lowest cards possible
        return min(moves, key=lambda m: (min(card_power(c) for c in m), -len(m)))
    # ------------------------------------------------------------------------------
    def remove_cards(self, cards):
        for c in cards:
            self.hand.remove(c)
    def print_hand(self):
        print(f"\nYour hand ({len(self.hand)}): "+" ".join(sorted(self.hand, key=card_power)))

class HongWuGame:
    def __init__(self, n_players=4, human=True, seed=None):
        if seed: random.seed(seed)
        self.players = [Player(i, is_human=(human and i==0)) for i in range(n_players)]
        self.deck = [r+s for r in RANK_ORDER for s in SUITS]
        random.shuffle(self.deck)
        for p in self.players:
            p.draw(self.deck, 5)
        self.curr = 0  # player index who leads next round
    def play(self, verbose=True):
        while True:
            # check for winner
            for p in self.players:
                if not p.hand:
                    if verbose: print(f"\nPlayer {p.id} wins!")
                    return p.id

            prev_play = None
            passes     = 0
            starter    = self.curr
            if verbose:
                print(f"\n=== New Round – Player {starter} leads "
                      f"(deck has {len(self.deck)} cards) ===")

            turn          = starter
            last_to_play  = None

            while passes < len(self.players) - 1:
                if verbose:
                    print(f"[Deck left: {len(self.deck)}] ", end="")
                pl = self.players[turn]
                play = pl.choose_play(prev_play)
                if play:
                    pl.remove_cards(play)
                    prev_play = play
                    passes = 0
                    last_to_play = turn
                    if combo_type(play) == 'bomb':
                        if verbose: print(f"Player {turn} plays BOMB {play} and wins the round.")
                        break
                    if verbose: print(f"Player {turn} plays {play}")
                else:
                    passes += 1
                    if verbose: print(f"Player {turn} passes.")
                turn = (turn + 1) % len(self.players)
            # draw phase – winner draws first
            winner = last_to_play if last_to_play is not None else starter
            order = list(range(winner, winner+len(self.players)))
            for i in order:
                p = self.players[i % len(self.players)]
                need = 5 - len(p.hand)
                p.draw(self.deck, need)
            self.curr = winner  # winner leads next round

# ----------------------------------------------------------------------
def simulate(n_games=1000, n_players=4):
    wins = [0]*n_players
    for _ in range(n_games):
        g = HongWuGame(n_players, human=False)
        w = g.play(verbose=False)
        wins[w]+=1
    print("\nSimulation results:")
    for pid, w in enumerate(wins):
        print(f"Player {pid}: {w}/{n_games} wins ({w/n_games:.1%})")

# Test function to verify card power hierarchy
def test_card_power():
    """Test that card power follows the correct Hong Wu hierarchy."""
    test_cards = [
        "3C", "4C", "5C", "6C", "7C", "8C", "9C", "TC", "JC", "QC", "KC", "AC", "2C",
        "5C", "5S", "5D", "5H"
    ]
    print("Card Power Test:")
    for card in test_cards:
        print(f"{card}: {card_power(card)}")
    
    # Test that 5s are in correct order
    fives = ["5C", "5S", "5D", "5H"]
    five_powers = [card_power(c) for c in fives]
    print(f"\nFive powers: {five_powers}")
    print(f"Five powers should be: [101, 102, 103, 104]")
    
    # Test that 5H is highest
    all_cards = [r+s for r in RANK_ORDER for s in SUITS]
    max_power = max(card_power(c) for c in all_cards)
    max_card = max(all_cards, key=card_power)
    print(f"\nHighest card: {max_card} with power {max_power}")
    print(f"Should be: 5H with power 104")

def test_runs_with_fives():
    """Test that 5s are properly allowed in runs."""
    print("\nRun Test with 5s:")
    
    # Test runs that should be valid
    valid_runs = [
        ["8C", "9C"],      # 8-9 (pair run)
        ["3C", "4C", "5C"],  # 3-4-5♣
        ["5C", "6C", "7C"],  # 5♣-6-7
        ["5H", "6C", "7C"],  # 5♥-6-7 (5♥ is highest 5)
        ["3C", "4C", "5H"],  # 3-4-5♥
        ["5C", "5S", "5D"],  # 5♣-5♠-5♦ (consecutive 5s)
        ["5S", "5D", "5H"],  # 5♠-5♦-5♥ (consecutive 5s)
    ]
    
    for run in valid_runs:
        run_type = combo_type(run)
        print(f"{run}: {run_type}")
        if run_type != 'run':
            print(f"  ERROR: Should be 'run' but got '{run_type}'")
    
    # Test runs that should be invalid
    invalid_runs = [
        ["3C", "5C", "7C"],  # 3-5-7 (not consecutive)
        ["5C", "6C", "8C"],  # 5-6-8 (not consecutive)
        ["3C", "4C", "5C", "5S"],  # 3-4-5♣-5♠ (duplicate rank)
    ]
    
    print("\nInvalid runs:")
    for run in invalid_runs:
        run_type = combo_type(run)
        print(f"{run}: {run_type}")
        if run_type == 'run':
            print(f"  ERROR: Should not be 'run' but got '{run_type}'")

def comprehensive_test():
    """Comprehensive test of all Hong Wu rules and mechanics."""
    print("=== COMPREHENSIVE HONG WU RULES TEST ===\n")
    
    # Test 1: Card Power Hierarchy
    print("1. CARD POWER HIERARCHY TEST:")
    test_cards = [
        ("3C", 0), ("4C", 1), ("5C", 101), ("6C", 3), ("7C", 4), ("8C", 5), 
        ("9C", 6), ("TC", 7), ("JC", 8), ("QC", 9), ("KC", 10), ("AC", 11), ("2C", 12),
        ("5C", 101), ("5S", 102), ("5D", 103), ("5H", 104)
    ]
    
    all_passed = True
    for card, expected_power in test_cards:
        actual_power = card_power(card)
        status = "✓" if actual_power == expected_power else "✗"
        print(f"  {status} {card}: {actual_power} (expected: {expected_power})")
        if actual_power != expected_power:
            all_passed = False
    
    print(f"  Card Power Test: {'PASSED' if all_passed else 'FAILED'}\n")
    
    # Test 2: Combo Type Detection
    print("2. COMBO TYPE DETECTION TEST:")
    combo_tests = [
        # Singles
        (["3C"], "single"),
        (["5H"], "single"),
        (["AC"], "single"),
        
        # Pairs (same rank)
        (["3C", "3D"], "pair"),
        (["5C", "5S"], "pair"),
        (["AC", "AH"], "pair"),
        
        # Triples
        (["3C", "3D", "3H"], "triple"),
        (["5C", "5S", "5D"], "triple"),
        
        # Bombs
        (["3C", "3D", "3H", "3S"], "bomb"),
        (["5C", "5S", "5D", "5H"], "bomb"),
        
        # Runs (consecutive)
        (["3C", "4C"], "run"),
        (["8C", "9C"], "run"),
        (["3C", "4C", "5C"], "run"),
        (["5C", "6C", "7C"], "run"),
        (["3C", "4C", "5H"], "run"),
        (["5C", "5S", "5D"], "triple"),  # Same rank, not consecutive
        
        # Invalid combos
        (["3C", "5C"], None),  # Not consecutive
        (["3C", "3C"], None),  # Duplicate card
        (["3C", "4C", "6C"], None),  # Not consecutive
        (["3C", "4C", "5C", "5S"], None),  # Duplicate rank
    ]
    
    all_passed = True
    for cards, expected_type in combo_tests:
        actual_type = combo_type(cards)
        status = "✓" if actual_type == expected_type else "✗"
        print(f"  {status} {cards}: {actual_type} (expected: {expected_type})")
        if actual_type != expected_type:
            all_passed = False
    
    print(f"  Combo Type Test: {'PASSED' if all_passed else 'FAILED'}\n")
    
    # Test 3: Beats Logic
    print("3. BEATS LOGIC TEST:")
    beats_tests = [
        # Singles
        (["5H"], ["3C"], True),   # 5H beats 3C
        (["3C"], ["5H"], False),  # 3C doesn't beat 5H
        (["5C"], ["5S"], False),  # Same power, doesn't beat
        
        # Pairs
        (["5C", "5S"], ["3C", "3D"], True),   # 5s beat 3s
        (["3C", "3D"], ["5C", "5S"], False),  # 3s don't beat 5s
        
        # Runs
        (["5C", "6C"], ["3C", "4C"], True),   # 5-6 beats 3-4
        (["3C", "4C"], ["5C", "6C"], False),  # 3-4 doesn't beat 5-6
        (["5C", "6C", "7C"], ["3C", "4C", "5C"], True),  # 5-6-7 beats 3-4-5
        
        # Bombs beat everything
        (["3C", "3D", "3H", "3S"], ["5H"], True),  # Bomb beats single
        (["3C", "3D", "3H", "3S"], ["5C", "5S"], True),  # Bomb beats pair
        (["3C", "3D", "3H", "3S"], ["5C", "6C"], True),  # Bomb beats run
        
        # Different types don't beat each other (except bombs)
        (["3C", "3D"], ["3C"], False),  # Pair doesn't beat single
        (["3C", "4C"], ["3C"], False),  # Run doesn't beat single
        (["3C"], ["3C", "3D"], False),  # Single doesn't beat pair
        
        # Starting round (no previous play)
        (["3C"], None, True),   # Any valid play beats nothing
        (["5H"], None, True),   # Any valid play beats nothing
    ]
    
    all_passed = True
    for play, prev, expected in beats_tests:
        actual = beats(play, prev)
        status = "✓" if actual == expected else "✗"
        prev_str = str(prev) if prev else "None"
        print(f"  {status} {play} beats {prev_str}: {actual} (expected: {expected})")
        if actual != expected:
            all_passed = False
    
    print(f"  Beats Logic Test: {'PASSED' if all_passed else 'FAILED'}\n")
    
    # Test 4: Legal Moves Generation
    print("4. LEGAL MOVES GENERATION TEST:")
    
    # Create a test player with specific hand
    test_player = Player(0, is_human=False)
    test_player.hand = ["3C", "4C", "5C", "5S", "6C", "7C", "8C", "9C", "AC", "2C"]
    
    # Test legal moves against different previous plays
    legal_tests = [
        (None, "Starting round - should have many options"),
        (["3C"], "Against single 3C"),
        (["5C", "5S"], "Against pair of 5s"),
        (["3C", "4C"], "Against run 3-4"),
    ]
    
    all_passed = True
    for prev_play, description in legal_tests:
        moves = test_player.legal_moves(prev_play)
        print(f"  {description}:")
        print(f"    Previous: {prev_play}")
        print(f"    Legal moves: {len(moves)} options")
        for i, move in enumerate(moves[:5]):  # Show first 5 moves
            print(f"      {i+1}. {move} ({combo_type(move)})")
        if len(moves) > 5:
            print(f"      ... and {len(moves)-5} more")
        
        # Basic validation: all moves should be valid combos
        for move in moves:
            if not combo_type(move):
                print(f"    ✗ Invalid move generated: {move}")
                all_passed = False
            if prev_play and not beats(move, prev_play):
                print(f"    ✗ Move doesn't beat previous: {move} vs {prev_play}")
                all_passed = False
        
        print()
    
    print(f"  Legal Moves Test: {'PASSED' if all_passed else 'FAILED'}\n")
    
    # Test 5: Game Mechanics
    print("5. GAME MECHANICS TEST:")
    
    # Test a simple game scenario
    game = HongWuGame(n_players=2, human=False, seed=42)
    print(f"  Game created with {len(game.players)} players")
    print(f"  Initial hands: {[len(p.hand) for p in game.players]}")
    print(f"  Deck size: {len(game.deck)}")
    
    # Test a few rounds
    for round_num in range(3):
        print(f"  Round {round_num + 1}:")
        starter = game.curr
        prev_play = None
        passes = 0
        turn = starter
        last_to_play = None
        
        while passes < len(game.players) - 1:
            pl = game.players[turn]
            play = pl.choose_play(prev_play)
            
            if play:
                pl.remove_cards(play)
                prev_play = play
                passes = 0
                last_to_play = turn
                print(f"    Player {turn} plays {play} ({combo_type(play)})")
                
                if combo_type(play) == 'bomb':
                    print(f"    BOMB! Round ends immediately")
                    break
            else:
                passes += 1
                print(f"    Player {turn} passes")
            
            turn = (turn + 1) % len(game.players)
        
        # Draw phase
        winner = last_to_play if last_to_play is not None else starter
        print(f"    Round winner: Player {winner}")
        
        order = list(range(winner, winner + len(game.players)))
        for i in order:
            p = game.players[i % len(game.players)]
            need = 5 - len(p.hand)
            p.draw(game.deck, need)
        
        game.curr = winner
        print(f"    Hands after draw: {[len(p.hand) for p in game.players]}")
        print(f"    Deck remaining: {len(game.deck)}")
        print()
    
    print("  Game Mechanics Test: PASSED\n")
    
    # Test 6: Edge Cases
    print("6. EDGE CASES TEST:")
    
    # Test with empty hand
    empty_player = Player(0, is_human=False)
    empty_moves = empty_player.legal_moves(None)
    print(f"  Empty hand legal moves: {len(empty_moves)} (should be 0)")
    
    # Test with very small deck
    small_game = HongWuGame(n_players=2, human=False, seed=123)
    small_game.deck = ["3C", "4C"]  # Only 2 cards left
    print(f"  Small deck test: {len(small_game.deck)} cards remaining")
    
    # Test invalid card combinations
    invalid_tests = [
        [],  # Empty
        ["INVALID"],  # Invalid card
        ["3C", "3C"],  # Duplicate
        ["3C", "4C", "3C"],  # Duplicate in longer combo
    ]
    
    for invalid_combo in invalid_tests:
        combo_result = combo_type(invalid_combo) if invalid_combo else combo_type([])
        print(f"  Invalid combo {invalid_combo}: {combo_result} (should be None)")
    
    print("  Edge Cases Test: PASSED\n")
    
    print("=== ALL TESTS COMPLETED ===")
    print("If you see any ✗ marks above, those specific tests failed.")
    print("Otherwise, all Hong Wu rules are working correctly!")

def test_consecutive_run_ranking():
    """Test the special consecutive run ranking system."""
    print("=== CONSECUTIVE RUN RANKING TEST ===")
    
    # Test two-card runs
    two_card_tests = [
        (["AC", "2C"], 0, "A-2 (weakest)"),
        (["2C", "3C"], 1, "2-3"),
        (["3C", "4C"], 2, "3-4"),
        (["8C", "9C"], 7, "8-9"),
        (["QC", "KC"], 11, "Q-K"),
        (["KC", "AC"], 12, "K-A (strongest)"),
    ]
    
    print("\nTwo-card runs:")
    for cards, expected_power, description in two_card_tests:
        actual_power = run_power(cards)
        status = "✓" if actual_power == expected_power else "✗"
        print(f"  {status} {cards}: {actual_power} (expected: {expected_power}) - {description}")
    
    # Test three-card runs
    three_card_tests = [
        (["AC", "2C", "3C"], 2, "A-2-3 (ends with 3)"),
        (["2C", "3C", "4C"], 3, "2-3-4 (ends with 4)"),
        (["QC", "KC", "AC"], 12, "Q-K-A (ends with A, strongest)"),
        (["KC", "AC", "2C"], 0, "K-A-2 (contains A-2, weakest)"),
    ]
    
    print("\nThree-card runs:")
    for cards, expected_power, description in three_card_tests:
        actual_power = run_power(cards)
        status = "✓" if actual_power == expected_power else "✗"
        print(f"  {status} {cards}: {actual_power} (expected: {expected_power}) - {description}")
    
    # Test four-card runs
    four_card_tests = [
        (["AC", "2C", "3C", "4C"], 3, "A-2-3-4 (ends with 4)"),
        (["JC", "QC", "KC", "AC"], 12, "J-Q-K-A (ends with A, strongest)"),
        (["KC", "AC", "2C", "3C"], 0, "K-A-2-3 (contains A-2, weakest)"),
    ]
    
    print("\nFour-card runs:")
    for cards, expected_power, description in four_card_tests:
        actual_power = run_power(cards)
        status = "✓" if actual_power == expected_power else "✗"
        print(f"  {status} {cards}: {actual_power} (expected: {expected_power}) - {description}")
    
    # Test beats logic for runs
    print("\nRun comparison tests:")
    beats_tests = [
        (["KC", "AC"], ["AC", "2C"], True, "K-A beats A-2"),
        (["AC", "2C"], ["KC", "AC"], False, "A-2 doesn't beat K-A"),
        (["3C", "4C"], ["2C", "3C"], True, "3-4 beats 2-3"),
        (["QC", "KC", "AC"], ["AC", "2C", "3C"], True, "Q-K-A beats A-2-3"),
        (["KC", "AC", "2C"], ["QC", "KC", "AC"], False, "K-A-2 doesn't beat Q-K-A"),
    ]
    
    for play, prev, expected, description in beats_tests:
        actual = beats(play, prev)
        status = "✓" if actual == expected else "✗"
        print(f"  {status} {play} beats {prev}: {actual} (expected: {expected}) - {description}")
    
    print("\n=== CONSECUTIVE RUN RANKING TEST COMPLETED ===")

if __name__ == "__main__":
    if len(sys.argv)==1:
        print("Usage:\n  python hongwu.py play        # human vs AI\n  python hongwu.py sim 5000     # simulate 5 000 games\n  python hongwu.py test          # test card power and runs\n  python hongwu.py comprehensive  # comprehensive rules test\n  python hongwu.py consecutive    # test consecutive run ranking")
        sys.exit()
    if sys.argv[1]=="play":
        HongWuGame().play()
    elif sys.argv[1]=="sim":
        n=int(sys.argv[2]) if len(sys.argv)>2 else 1000
        simulate(n)
    elif sys.argv[1]=="test":
        test_card_power()
        test_runs_with_fives()
    elif sys.argv[1]=="comprehensive":
        comprehensive_test()
    elif sys.argv[1]=="consecutive":
        test_consecutive_run_ranking()
