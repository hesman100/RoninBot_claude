/**
 * Country Guessing Game - Game Logic
 * Handles the gameplay for the country guessing game (map, flag, capital modes)
 */

// Main game manager
const GameManager = {
    // Game state
    currentGame: null,
    timeRemaining: 0,
    timerInterval: null,
    gameMode: null,
    options: [],
    correctAnswer: null,
    imageUrl: null,
    
    // Start a new game with the specified mode
    startGame: function(mode) {
        this.gameMode = mode;
        this.stopTimer(); // In case there's a timer running
        
        // Show loading state
        document.getElementById('game-image-container').innerHTML = '<p>Loading game...</p>';
        document.getElementById('options-container').innerHTML = '';
        
        // Request a new game from the server
        fetch(`/api/game/${mode}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    this.setupGameUI(data);
                    this.startTimer(data.timer || 30);
                } else {
                    this.showError(data.message || 'Error starting game');
                }
            })
            .catch(error => {
                console.error('Error starting game:', error);
                this.showError('Network error. Please try again.');
            });
    },
    
    // Set up the game UI with data from the server
    setupGameUI: function(data) {
        this.options = data.options;
        this.correctAnswer = data.correct_answer; // Will be null until answered
        this.imageUrl = data.image_url;
        
        // Display the game image
        const imageContainer = document.getElementById('game-image-container');
        imageContainer.innerHTML = `<img src="${this.imageUrl}" alt="${this.gameMode} game" class="game-image">`;
        
        // Create option buttons
        const optionsContainer = document.getElementById('options-container');
        optionsContainer.innerHTML = '';
        
        this.options.forEach(option => {
            const button = document.createElement('button');
            button.className = 'option-button button';
            button.textContent = option;
            button.onclick = () => this.submitAnswer(option);
            optionsContainer.appendChild(button);
        });
        
        // Show the question text based on game mode
        let questionText = 'Which country is this?';
        if (this.gameMode === 'capital') {
            questionText = 'What is the capital city of this country?';
        }
        document.getElementById('question-text').textContent = questionText;
    },
    
    // Submit an answer to the server
    submitAnswer: function(answer) {
        this.stopTimer();
        
        // Disable all option buttons to prevent multiple submissions
        const buttons = document.querySelectorAll('.option-button');
        buttons.forEach(button => {
            button.disabled = true;
            button.style.opacity = '0.6';
            if (button.textContent === answer) {
                button.style.border = '2px solid yellow';
            }
        });
        
        // Send the answer to the server
        fetch('/api/game/answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                mode: this.gameMode,
                answer: answer
            })
        })
        .then(response => response.json())
        .then(data => {
            this.showResult(data);
        })
        .catch(error => {
            console.error('Error submitting answer:', error);
            this.showError('Network error. Please try again.');
        });
    },
    
    // Start the game timer
    startTimer: function(seconds) {
        this.timeRemaining = seconds;
        this.updateTimerDisplay();
        
        this.timerInterval = setInterval(() => {
            this.timeRemaining--;
            this.updateTimerDisplay();
            
            if (this.timeRemaining <= 0) {
                this.handleTimeout();
            }
        }, 1000);
    },
    
    // Stop the timer
    stopTimer: function() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    },
    
    // Update the timer display
    updateTimerDisplay: function() {
        const timerElement = document.getElementById('timer');
        if (timerElement) {
            timerElement.textContent = `Time: ${this.timeRemaining}s`;
            
            // Change color when time is running low
            if (this.timeRemaining <= 5) {
                timerElement.style.color = '#F44336';
            } else {
                timerElement.style.color = '#fff';
            }
        }
    },
    
    // Handle timeout when the timer reaches zero
    handleTimeout: function() {
        this.stopTimer();
        
        // Disable all option buttons
        const buttons = document.querySelectorAll('.option-button');
        buttons.forEach(button => {
            button.disabled = true;
            button.style.opacity = '0.6';
        });
        
        // Notify the server about the timeout
        fetch('/api/game/timeout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                mode: this.gameMode
            })
        })
        .then(response => response.json())
        .then(data => {
            this.showResult(data);
        })
        .catch(error => {
            console.error('Error handling timeout:', error);
            this.showError('Network error. Please try again.');
        });
    },
    
    // Show the game result
    showResult: function(data) {
        const resultContainer = document.getElementById('result-container');
        resultContainer.style.display = 'block';
        
        // Show whether the answer was correct or not
        const resultText = document.getElementById('result-text');
        if (data.correct) {
            resultText.className = 'result-correct';
            resultText.textContent = '✅ Correct!';
        } else {
            resultText.className = 'result-incorrect';
            resultText.textContent = '❌ Incorrect!';
        }
        
        // Show country details
        const countryDetails = document.getElementById('country-details');
        const details = data.country_details;
        
        countryDetails.innerHTML = `
            <p>🏳️ Country: ${details.name}</p>
            <p>🏙️ Capital: ${details.capital}</p>
            <p>🌍 Region: ${details.region}</p>
            <p>👥 Population: ${this.formatPopulation(details.population)}</p>
            <p>📏 Area: ${this.formatArea(details.area)}</p>
            <p>Bot Version: ${data.version}</p>
        `;
        
        // Highlight the correct answer
        const buttons = document.querySelectorAll('.option-button');
        buttons.forEach(button => {
            if (button.textContent === data.correct_answer) {
                button.style.border = '2px solid #4CAF50';
                button.style.backgroundColor = 'rgba(76, 175, 80, 0.3)';
            }
        });
        
        // Show play again buttons
        document.getElementById('play-again-container').style.display = 'block';
    },
    
    // Show an error message
    showError: function(message) {
        const resultContainer = document.getElementById('result-container');
        resultContainer.style.display = 'block';
        
        const resultText = document.getElementById('result-text');
        resultText.className = 'result-incorrect';
        resultText.textContent = `Error: ${message}`;
        
        // Show play again buttons
        document.getElementById('play-again-container').style.display = 'block';
    },
    
    // Helper function to format population numbers
    formatPopulation: function(population) {
        if (population >= 1000000000) {
            return `${(population / 1000000000).toFixed(1)} billion`;
        } else if (population >= 1000000) {
            return `${(population / 1000000).toFixed(1)} million`;
        } else if (population >= 1000) {
            return `${(population / 1000).toFixed(1)} thousand`;
        }
        return population.toString();
    },
    
    // Helper function to format area values
    formatArea: function(area) {
        return `${area.toLocaleString()} km²`;
    }
};

// Function to start a new game
function playGame(mode) {
    // Hide any previous results
    document.getElementById('result-container').style.display = 'none';
    document.getElementById('play-again-container').style.display = 'none';
    
    // Start the game
    GameManager.startGame(mode);
}

// Function to create a guest session before playing
function createGuestSession() {
    fetch('/api/user/guest', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('Created guest session:', data);
        window.location.href = "/game/map";
    })
    .catch(error => {
        console.error('Error creating guest session:', error);
        alert('Error creating guest session. Please try again.');
    });
}

// Function to navigate back to the main menu
function goToMenu() {
    window.location.href = "/";
}

// Initialize event listeners when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // If we're on a game page, check the URL for the game mode and start it
    const path = window.location.pathname;
    const gameModeParts = path.match(/\/game\/(map|flag|capital)/);
    
    if (gameModeParts && gameModeParts.length > 1) {
        const mode = gameModeParts[1];
        playGame(mode);
    }
});
