#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, session
import random
import json
from hongwu import HongWuGame, Player, combo_type, card_power, beats
import threading
import time

app = Flask(__name__)
app.secret_key = 'hongwu_secret_key_2024'

# Global game state
active_games = {}

def get_game_state_dict(game_id):
    if game_id not in active_games:
        return {'error': 'Game not found'}
    game_data = active_games[game_id]
    game = game_data['game']
    
    # Check for winner
    for p in game.players:
        if not p.hand:
            game_data['winner'] = p.id
            game_data['game_state'] = 'finished'
    
    # If player 0 is human, include their hand
    hand = None
    if game.players[0].is_human:
        hand = game.players[0].hand
    
    # Get current highest play for display
    current_play = None
    if game_data.get('current_play'):
        current_play = game_data['current_play']
    
    return {
        'players': [{'id': p.id, 'hand_size': len(p.hand), 'is_human': p.is_human} for p in game.players],
        'current_player': game.curr,
        'deck_size': len(game.deck),
        'winner': game_data.get('winner'),
        'game_state': game_data.get('game_state', 'playing'),
        'last_action': game_data.get('last_action'),
        'hand': hand,
        'current_play': current_play,
        'passes': game_data.get('passes', 0)
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game')
def game():
    return render_template('game.html')

@app.route('/analysis')
def analysis():
    return render_template('analysis.html')

@app.route('/rules')
def rules():
    return render_template('rules.html')

@app.route('/api/start_game', methods=['POST'])
def start_game():
    data = request.get_json()
    n_players = data.get('n_players', 4)
    human = data.get('human', True)
    game_id = f"game_{int(time.time())}_{random.randint(1000, 9999)}"
    game = HongWuGame(n_players=n_players, human=human)
    
    # Find the player with the highest card to start
    highest_card = None
    starting_player = 0
    
    for i, player in enumerate(game.players):
        for card in player.hand:
            if highest_card is None or card_power(card) > card_power(highest_card):
                highest_card = card
                starting_player = i
    
    # Set the starting player
    game.curr = starting_player
    
    active_games[game_id] = {
        'game': game,
        'game_state': 'playing',
        'last_action': None,
        'winner': None,
        'passes': 0,
        'current_play': None,
        'round_starter': starting_player,
        'last_card_player': None  # Track who played the last cards
    }
    session['game_id'] = game_id
    game_state = get_game_state_dict(game_id)
    print(f"DEBUG: Game started with human={human}, starting_player={starting_player} (highest card: {highest_card}), hand={game_state.get('hand')}")
    
    # If the starting player is AI, process their turn immediately
    if starting_player != 0 and not game.players[starting_player].is_human:
        print(f"DEBUG: Starting player {starting_player} is AI, processing their turn")
        # Process the AI turn
        ai_play = game.players[starting_player].choose_play(None)  # No previous play to beat
        
        if ai_play:
            game.players[starting_player].remove_cards(ai_play)
            active_games[game_id]['current_play'] = ai_play
            active_games[game_id]['last_action'] = {
                'player_id': starting_player,
                'cards': ai_play,
                'type': combo_type(ai_play)
            }
            active_games[game_id]['last_card_player'] = starting_player  # Track who played cards
            print(f"DEBUG: AI Player {starting_player} starts with {ai_play}")
            
            # Move to next player
            game.curr = (starting_player + 1) % len(game.players)
        else:
            # AI passes (unlikely but possible)
            active_games[game_id]['passes'] = 1
            active_games[game_id]['last_action'] = {
                'player_id': starting_player,
                'action': 'pass'
            }
            print(f"DEBUG: AI Player {starting_player} passes to start")
            
            # Move to next player
            game.curr = (starting_player + 1) % len(game.players)
        
        # Update game state after AI move
        game_state = get_game_state_dict(game_id)
    
    return jsonify({'game_id': game_id, 'game_state': game_state})

@app.route('/api/game_state/<game_id>')
def get_game_state(game_id):
    game_state = get_game_state_dict(game_id)
    return jsonify(game_state)

@app.route('/api/ai_turn/<game_id>')
def process_ai_turn(game_id):
    """Process a single AI turn and return the updated game state."""
    print(f"DEBUG: AI turn endpoint called for game {game_id}")
    
    if game_id not in active_games:
        print(f"DEBUG: Game {game_id} not found")
        return jsonify({'error': 'Game not found'})
    
    game_data = active_games[game_id]
    game = game_data['game']
    
    # Check if current player is AI and game is not finished
    game_state = get_game_state_dict(game_id)
    print(f"DEBUG: Current player: {game_state.get('current_player')}, Winner: {game_state.get('winner')}")
    
    if (game_state.get('winner') is None and 
        game_state.get('current_player') is not None):
        
        current_player = game.players[game_state['current_player']]
        print(f"DEBUG: Current player object - ID: {current_player.id}, Is human: {current_player.is_human}")
        
        if not current_player.is_human:
            print(f"DEBUG: Processing AI turn for Player {game_state['current_player']}")
            
            # AI player's turn - make them play
            ai_play = current_player.choose_play(game_data.get('current_play'))
            print(f"DEBUG: AI chose play: {ai_play}")
            
            if ai_play:
                current_player.remove_cards(ai_play)
                game_data['current_play'] = ai_play
                game_data['passes'] = 0
                game_data['last_action'] = {
                    'player_id': game_state['current_player'],
                    'cards': ai_play,
                    'type': combo_type(ai_play)
                }
                game_data['last_card_player'] = game_state['current_player']  # Track who played cards
                print(f"DEBUG: Recorded AI play action for Player {game_state['current_player']}: {ai_play}")
                
                print(f"DEBUG: AI Player {game_state['current_player']} plays {ai_play}")
                
                # If bomb played, round ends immediately
                if combo_type(ai_play) == 'bomb':
                    end_round(game_data)
                else:
                    # Move to next player (clockwise)
                    next_player = (game.curr + 1) % len(game.players)
                    print(f"DEBUG: Moving from Player {game.curr} to Player {next_player} (clockwise)")
                    game.curr = next_player
            else:
                # AI passes
                game_data['passes'] = game_data.get('passes', 0) + 1
                game_data['last_action'] = {
                    'player_id': game_state['current_player'],
                    'action': 'pass'
                }
                print(f"DEBUG: Recorded AI pass action for Player {game_state['current_player']}")
                
                # Check if round should end (all but one player passed)
                if game_data['passes'] >= len(game.players) - 1:
                    print(f"DEBUG: Round should end! passes: {game_data['passes']}, players: {len(game.players)}")
                    end_round(game_data)
                else:
                    # Move to next player (clockwise)
                    next_player = (game.curr + 1) % len(game.players)
                    print(f"DEBUG: Moving from Player {game.curr} to Player {next_player} (clockwise)")
                    game.curr = next_player
        else:
            print(f"DEBUG: Current player {game_state['current_player']} is human, not processing AI turn")
    else:
        print(f"DEBUG: Game finished or no current player - winner: {game_state.get('winner')}, current_player: {game_state.get('current_player')}")
    
    return jsonify(get_game_state_dict(game_id))

@app.route('/play', methods=['POST'])
def play_cards():
    data = request.get_json()
    game_id = data.get('game_id')
    cards = data.get('cards', [])
    
    if game_id not in active_games:
        return jsonify({'error': 'Game not found'})
    
    game_data = active_games[game_id]
    game = game_data['game']
    
    # Check for winner
    for p in game.players:
        if not p.hand:
            game_data['winner'] = p.id
            game_data['game_state'] = 'finished'
            return jsonify(get_game_state_dict(game_id))
    
    # Verify it's the human player's turn
    current_player = game.players[game.curr]
    if not current_player.is_human:
        return jsonify({'error': 'Not your turn'})
    
    print(f"DEBUG: Human play, cards: {cards}, current_play: {game_data.get('current_play')}")
    
    if not cards:
        # Human passes
        game_data['passes'] = game_data.get('passes', 0) + 1
        
        # Record the action
        game_data['last_action'] = {
            'player_id': game.curr,
            'action': 'pass'
        }
        print(f"DEBUG: Recorded pass action for Player {game.curr}")
        
        # Check if round should end (all but one player passed)
        if game_data['passes'] >= len(game.players) - 1:
            print(f"DEBUG: Round should end! passes: {game_data['passes']}, players: {len(game.players)}")
            end_round(game_data)
        else:
            # Move to next player (clockwise)
            next_player = (game.curr + 1) % len(game.players)
            print(f"DEBUG: Moving from Player {game.curr} to Player {next_player} (clockwise)")
            game.curr = next_player
        
    else:
        # Human plays cards
        # Validate the play
        if not all(card in current_player.hand for card in cards):
            return jsonify({'error': 'Invalid cards'})
        
        if not combo_type(cards):
            return jsonify({'error': 'Invalid combination'})
        
        if not beats(cards, game_data.get('current_play')):
            return jsonify({'error': 'Cards do not beat previous play'})
        
        # Remove cards from hand
        current_player.remove_cards(cards)
        play_type = combo_type(cards)
        
        # Update current play and reset passes
        game_data['current_play'] = cards
        game_data['passes'] = 0
        game_data['last_action'] = {
            'player_id': game.curr,
            'action': 'play',
            'cards': cards,
            'type': play_type
        }
        game_data['last_card_player'] = game.curr  # Track who played cards
        print(f"DEBUG: Recorded play action for Player {game.curr}: {cards}")
        
        print(f"DEBUG: Human plays {cards} ({play_type})")
        
        # If bomb played, round ends immediately
        if play_type == 'bomb':
            print("DEBUG: Bomb played, ending round immediately")
            end_round(game_data)
        else:
            # Move to next player (clockwise)
            next_player = (game.curr + 1) % len(game.players)
            print(f"DEBUG: Moving from Player {game.curr} to Player {next_player} (clockwise)")
            game.curr = next_player
    
    return jsonify(get_game_state_dict(game_id))

def end_round(game_data):
    """End the current round and draw cards for all players."""
    game = game_data['game']
    
    # Determine winner of round - who played the last actual cards
    last_action = game_data.get('last_action')
    last_card_player = game_data.get('last_card_player')
    print(f"DEBUG: end_round called, last_action: {last_action}")
    print(f"DEBUG: last_card_player: {last_card_player}")
    
    if last_card_player is not None:
        # The last player who played cards wins the round
        winner = last_card_player
        print(f"DEBUG: Winner determined by last card player - Player {winner}")
    else:
        # If no one played cards (all passed), the starter wins
        winner = game_data.get('round_starter', 0)
        print(f"DEBUG: Winner determined by starter (all passed) - Player {winner}")
    
    print(f"DEBUG: Round ended, winner: Player {winner}")
    print(f"DEBUG: Previous round_starter was: {game_data.get('round_starter')}")
    
    # Draw cards starting from winner
    order = list(range(winner, winner + len(game.players)))
    for i in order:
        p = game.players[i % len(game.players)]
        need = 5 - len(p.hand)
        if need > 0 and game.deck:
            p.draw(game.deck, need)
            print(f"DEBUG: Player {p.id} drew {need} cards, hand size now: {len(p.hand)}")
    
    # Winner leads next round
    game.curr = winner
    
    # Reset for next round
    game_data['passes'] = 0
    game_data['round_starter'] = winner
    game_data['current_play'] = None
    game_data['last_card_player'] = None  # Reset for new round
    game_data['last_action'] = {
        'player_id': winner,
        'action': 'round_end',
        'message': f'Round over! Player {winner} is the leader.'
    }
    
    print(f"DEBUG: New round started, player {winner} leads")
    print(f"DEBUG: New round_starter set to: {game_data['round_starter']}")

@app.route('/api/simulate', methods=['POST'])
def simulate_games():
    data = request.get_json()
    n_games = data.get('n_games', 1000)
    n_players = data.get('n_players', 4)
    
    wins = [0] * n_players
    game_lengths = []
    bomb_plays = 0
    
    for _ in range(n_games):
        game = HongWuGame(n_players=n_players, human=False)
        rounds = 0
        bombs_this_game = 0
        
        while True:
            # Check for winner
            winner = None
            for p in game.players:
                if not p.hand:
                    winner = p.id
                    break
            
            if winner is not None:
                wins[winner] += 1
                game_lengths.append(rounds)
                bomb_plays += bombs_this_game
                break
            
            # Play round
            prev_play = None
            passes = 0
            starter = game.curr
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
                    
                    if combo_type(play) == 'bomb':
                        bombs_this_game += 1
                        break
                else:
                    passes += 1
                
                turn = (turn + 1) % len(game.players)
            
            # Draw phase
            winner_round = last_to_play if last_to_play is not None else starter
            order = list(range(winner_round, winner_round + len(game.players)))
            for i in order:
                p = game.players[i % len(game.players)]
                need = 5 - len(p.hand)
                p.draw(game.deck, need)
            
            game.curr = winner_round
            rounds += 1
    
    avg_length = sum(game_lengths) / len(game_lengths) if game_lengths else 0
    bomb_rate = bomb_plays / n_games if n_games > 0 else 0
    
    return jsonify({
        'wins': wins,
        'total_games': n_games,
        'avg_game_length': round(avg_length, 2),
        'bomb_rate': round(bomb_rate, 4),
        'win_percentages': [round(w/n_games*100, 2) for w in wins]
    })

@app.route('/api/probability_analysis')
def probability_analysis():
    # Calculate various probabilities
    results = {}
    
    # Probability of getting specific cards in 5-card hand
    total_hands = 2598960  # C(52,5)
    
    # Probability of getting at least one 5
    # Calculate probability of getting NO fives, then subtract from 1
    # C(48,5) = hands with no fives
    hands_with_no_five = (48 * 47 * 46 * 45 * 44) // (5 * 4 * 3 * 2)
    hands_with_five = total_hands - hands_with_no_five
    results['at_least_one_five'] = round(hands_with_five / total_hands * 100, 2)
    
    # Probability of getting 5♥ specifically
    hands_with_5h = (51 * 50 * 49 * 48) // (4 * 3 * 2)  # C(51,4)
    results['five_hearts'] = round(hands_with_5h / total_hands * 100, 2)
    
    # Probability of getting a bomb
    hands_with_bomb = 0
    for rank in "3456789TJQKA2":
        hands_with_bomb += (48)  # 4 cards of same rank + 1 other
    results['bomb'] = round(hands_with_bomb / total_hands * 100, 4)
    
    # Probability of getting a run of 3+
    # This is complex, so we'll estimate
    results['run_3_plus'] = "~15-20%"  # Approximate
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 