# Hong Wu (红五) - Red Five Card Game

A beautiful web application for playing and analyzing the classic Chinese card game Hong Wu (红五), where the Red Five (5♥) reigns supreme!

## 🎮 Features

- **Interactive Gameplay**: Play Hong Wu against AI opponents with a beautiful, responsive interface
- **Probability Analysis**: Explore the mathematics behind the game with interactive charts and statistics
- **Comprehensive Rules**: Complete rulebook with examples and strategic insights
- **Game Simulation**: Run thousands of games to analyze win rates and game statistics
- **Modern UI**: Beautiful, responsive design that works on desktop and mobile

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. **Clone or download the project**

   ```bash
   git clone <repository-url>
   cd HongWu
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**

   ```bash
   python app.py
   ```

4. **Open your browser**
   Navigate to `http://localhost:5000`

## 🎯 How to Play

### Game Overview

- **Players**: 3-5 (4 is standard)
- **Deck**: Standard 52-card deck
- **Hand Size**: Always 5 cards
- **Goal**: Be the first to empty your hand

### Card Power Hierarchy

```
3 < 4 < 5 < 6 < 7 < 8 < 9 < 10 < J < Q < K < A < 2 < 5♣ < 5♠ < 5♦ < 5♥
```

The four 5s are special and outrank every other card. The Red Five (5♥) is the highest card in the game.

### Legal Play Categories

1. **Single**: 1 card
2. **Pair**: 2 identical ranks
3. **Triple**: 3 identical ranks
4. **Bomb (炸弹)**: 4 identical ranks (beats anything!)
5. **Run**: 2+ consecutive ranks (no 5s allowed)

### Game Flow

1. Each player starts with 5 cards
2. Leader plays any legal combination
3. Players must play the same category at higher power or pass
4. Bombs can be played anytime and win the round immediately
5. Round ends when all but one player pass
6. Winner draws first, others draw in pass order
7. First to empty their hand wins!

## 📊 Analysis Features

### Probability Analysis

- Chance of getting specific cards in your hand
- Probability of bombs, runs, and other combinations
- Strategic insights based on mathematical analysis

### Game Simulation

- Run thousands of games to analyze win rates
- Compare different player counts
- View average game length and bomb frequency
- Interactive charts and statistics

## 🏗️ Project Structure

```
HongWu/
├── app.py                 # Flask web application
├── hongwu.py             # Core game logic
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── templates/           # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── game.html
│   ├── analysis.html
│   └── rules.html
└── static/              # Static assets
    └── css/
        └── style.css
```

## 🎨 Technology Stack

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Styling**: Bootstrap 5, Custom CSS
- **Charts**: Chart.js
- **Icons**: Font Awesome

## 🔧 Development

### Running in Development Mode

```bash
python app.py
```

The application will run on `http://localhost:5000` with debug mode enabled.

### File Structure

- `app.py`: Main Flask application with API endpoints
- `hongwu.py`: Core game logic and AI players
- `templates/`: HTML templates for each page
- `static/css/style.css`: Custom styling

### API Endpoints

- `GET /`: Home page
- `GET /game`: Game interface
- `GET /analysis`: Probability analysis
- `GET /rules`: Game rules
- `POST /api/start_game`: Start a new game
- `GET /api/game_state/<game_id>`: Get current game state
- `POST /api/play_turn`: Make a move
- `POST /api/end_round`: End current round
- `POST /api/simulate`: Run game simulations
- `GET /api/probability_analysis`: Get probability data

## 🎯 Strategic Insights

### Key Strategies

1. **Early Tempo**: Don't wait for bombs - they're extremely rare (~0.024% chance)
2. **Five Cards**: Any five is valuable; 34% chance to start with at least one
3. **Runs**: Two-card runs are powerful; A-2 is weakest, K-A is strongest
4. **Passing**: Early passes can be profitable for better draw order

### Probability Highlights

- **At least one 5**: 34.0%
- **Red Five (5♥)**: 9.6%
- **Bomb in hand**: 0.024%
- **Run of 3+**: ~15-20%

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Original Hong Wu game rules and community
- Bootstrap and Chart.js for the beautiful UI components
- Font Awesome for the icons

---

**Enjoy playing Hong Wu (红五) - The Red Five Card Game!** 🃏♥️
