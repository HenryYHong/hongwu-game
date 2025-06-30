from flask import Flask, render_template, request, jsonify
import sys
import os
import json

# Add the parent directory to the path so we can import hongwu
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hongwu import HongWuGame

app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')

# Global game instance
game_instance = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game')
def game():
    return render_template('game.html')

@app.route('/rules')
def rules():
    return render_template('rules.html')

@app.route('/analysis')
def analysis():
    return render_template('analysis.html')

@app.route('/api/start_game', methods=['POST'])
def start_game():
    global game_instance
    data = request.get_json()
    player_count = int(data.get('player_count', 4))
    human_player = data.get('human_player', True)
    
    game_instance = HongWuGame(player_count, human_player)
    game_state = game_instance.get_state()
    return jsonify(game_state)

@app.route('/api/play_cards', methods=['POST'])
def play_cards():
    global game_instance
    if not game_instance:
        return jsonify({'error': 'No active game'}), 400
    
    data = request.get_json()
    card_indices = data.get('card_indices', [])
    
    success = game_instance.play_cards(card_indices)
    if success:
        game_state = game_instance.get_state()
        return jsonify(game_state)
    else:
        return jsonify({'error': 'Invalid play'}), 400

@app.route('/api/pass_turn', methods=['POST'])
def pass_turn():
    global game_instance
    if not game_instance:
        return jsonify({'error': 'No active game'}), 400
    
    success = game_instance.pass_turn()
    if success:
        game_state = game_instance.get_state()
        return jsonify(game_state)
    else:
        return jsonify({'error': 'Cannot pass'}), 400

@app.route('/api/ai_turn', methods=['POST'])
def ai_turn():
    global game_instance
    if not game_instance:
        return jsonify({'error': 'No active game'}), 400
    
    success = game_instance.ai_turn()
    if success:
        game_state = game_instance.get_state()
        return jsonify(game_state)
    else:
        return jsonify({'error': 'AI turn failed'}), 400

@app.route('/api/get_state', methods=['GET'])
def get_state():
    global game_instance
    if not game_instance:
        return jsonify({'error': 'No active game'}), 400
    
    game_state = game_instance.get_state()
    return jsonify(game_state)

# Vercel handler
def handler(request, context):
    return app(request, context)

if __name__ == '__main__':
    app.run(debug=True) 