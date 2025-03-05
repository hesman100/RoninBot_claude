/**
 * Example Android code for connecting to the country game API
 * This shows the basic structure of the API client, data models,
 * and view model for the game functionality
 */

// API Interface using Retrofit
interface CountryGameApiService {
    @GET("game/start")
    suspend fun startGame(
        @Query("mode") mode: String
    ): GameInitResponse
    
    @POST("game/answer")
    suspend fun submitAnswer(
        @Body answerRequest: AnswerRequest
    ): AnswerResponse
    
    @GET("leaderboard")
    suspend fun getLeaderboard(
        @Query("mode") mode: String = "all",
        @Query("limit") limit: Int = 10
    ): LeaderboardResponse
    
    @GET("images/{type}/{countryId}")
    suspend fun getImage(
        @Path("type") type: String,
        @Path("countryId") countryId: Int,
        @Query("width") width: Int? = null,
        @Query("height") height: Int? = null
    ): ResponseBody
}

// --- Data Models ---

// Response when starting a new game
data class GameInitResponse(
    val game_id: String,
    val mode: String,
    val options: List<String>,
    val timeout: Int,
    val expires_at: Long,
    val image_url: String? = null,
    val country_name: String? = null  // Used in capital mode
)

// Request to submit an answer
data class AnswerRequest(
    val game_id: String,
    val selected_option: String,
    val player_name: String
)

// Response after submitting an answer
data class AnswerResponse(
    val correct: Boolean,
    val correct_answer: String,
    val elapsed_time: Double,
    val country_details: CountryDetails
)

// Country details returned with game results
data class CountryDetails(
    val name: String,
    val capital: String,
    val region: String,
    val population: Long,
    val area: Double
)

// Leaderboard response
data class LeaderboardResponse(
    val leaderboard: List<LeaderboardEntry>
)

data class LeaderboardEntry(
    val player_name: String,
    val score: Int,
    val games_played: Int,
    val games_won: Int
)

// --- API Client Configuration ---

// API client with authentication interceptor
class CountryGameApiClient(private val context: Context) {
    
    private val apiKey = BuildConfig.API_KEY
    
    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor { chain ->
            val original = chain.request()
            val requestBuilder = original.newBuilder()
                .header("X-API-Key", apiKey)
                .method(original.method, original.body)
            
            chain.proceed(requestBuilder.build())
        }
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .build()
    
    private val retrofit = Retrofit.Builder()
        .baseUrl(BuildConfig.API_BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
    
    val apiService: CountryGameApiService = retrofit.create(CountryGameApiService::class.java)
}

// --- Game ViewModel ---

class GameViewModel(
    private val apiClient: CountryGameApiClient,
    private val imageLoader: ImageLoader,
    private val preferencesManager: PreferencesManager
) : ViewModel() {
    
    // Game state
    private val _gameState = MutableLiveData<GameState>()
    val gameState: LiveData<GameState> = _gameState
    
    // Timer for game countdown
    private var countDownTimer: CountDownTimer? = null
    
    // Current game details
    private var currentGameId: String? = null
    private var currentMode: String? = null
    
    // Start a new game
    fun startGame(mode: String) {
        viewModelScope.launch {
            try {
                _gameState.value = GameState.Loading
                
                // Call API to start a new game
                val response = apiClient.apiService.startGame(mode)
                
                // Store game ID and mode
                currentGameId = response.game_id
                currentMode = response.mode
                
                // Load image if applicable
                val imageUrl = response.image_url
                val bitmap = if (imageUrl != null) {
                    // Check if image is cached
                    val cachedImage = imageLoader.getCachedImage(imageUrl)
                    if (cachedImage != null) {
                        cachedImage
                    } else {
                        // Download and cache the image
                        val imageResponse = apiClient.apiService.getImage(
                            type = if (mode == "flag") "flag" else "map",
                            countryId = extractCountryId(imageUrl),
                            width = 800  // Reasonable size for most devices
                        )
                        
                        // Convert to bitmap and cache
                        val bitmap = BitmapFactory.decodeStream(imageResponse.byteStream())
                        imageLoader.cacheImage(imageUrl, bitmap)
                        bitmap
                    }
                } else null
                
                // Update game state
                _gameState.value = GameState.InProgress(
                    gameId = response.game_id,
                    mode = response.mode,
                    options = response.options,
                    countryName = response.country_name,
                    image = bitmap,
                    timeoutSeconds = response.timeout
                )
                
                // Start countdown timer
                startCountdownTimer(response.expires_at)
                
            } catch (e: Exception) {
                _gameState.value = GameState.Error("Failed to start game: ${e.message}")
            }
        }
    }
    
    // Submit an answer
    fun submitAnswer(selectedOption: String) {
        val gameId = currentGameId ?: return
        
        viewModelScope.launch {
            try {
                // Cancel the timer
                countDownTimer?.cancel()
                
                // Get player name from preferences
                val playerName = preferencesManager.getPlayerName() ?: "Guest"
                
                // Call API to submit answer
                val request = AnswerRequest(
                    game_id = gameId,
                    selected_option = selectedOption,
                    player_name = playerName
                )
                
                val response = apiClient.apiService.submitAnswer(request)
                
                // Update game state
                _gameState.value = GameState.Completed(
                    isCorrect = response.correct,
                    correctAnswer = response.correct_answer,
                    elapsedTime = response.elapsed_time,
                    countryDetails = response.country_details
                )
                
                // Clear current game
                currentGameId = null
                
            } catch (e: Exception) {
                _gameState.value = GameState.Error("Failed to submit answer: ${e.message}")
            }
        }
    }
    
    // Get leaderboard
    fun getLeaderboard(mode: String = "all") {
        viewModelScope.launch {
            try {
                _gameState.value = GameState.LoadingLeaderboard
                
                // Call API to get leaderboard
                val response = apiClient.apiService.getLeaderboard(mode)
                
                // Update game state
                _gameState.value = GameState.Leaderboard(
                    entries = response.leaderboard,
                    mode = mode
                )
                
            } catch (e: Exception) {
                _gameState.value = GameState.Error("Failed to load leaderboard: ${e.message}")
            }
        }
    }
    
    // Start countdown timer
    private fun startCountdownTimer(expiresAt: Long) {
        // Cancel any existing timer
        countDownTimer?.cancel()
        
        // Calculate time remaining
        val timeRemaining = expiresAt - System.currentTimeMillis() / 1000
        if (timeRemaining <= 0) {
            // Game already expired
            _gameState.value = GameState.Timeout
            return
        }
        
        // Create new timer
        countDownTimer = object : CountDownTimer(timeRemaining * 1000, 1000) {
            override fun onTick(millisUntilFinished: Long) {
                // Update time remaining
                val currentState = _gameState.value
                if (currentState is GameState.InProgress) {
                    _gameState.value = currentState.copy(
                        timeRemaining = millisUntilFinished / 1000
                    )
                }
            }
            
            override fun onFinish() {
                // Game timed out
                _gameState.value = GameState.Timeout
                
                // Clear current game
                currentGameId = null
            }
        }.start()
    }
    
    // Extract country ID from image URL
    private fun extractCountryId(imageUrl: String): Int {
        // URL format: /api/images/[type]/[countryId]
        val parts = imageUrl.split("/")
        return parts.lastOrNull()?.toIntOrNull() ?: 1
    }
    
    // Clean up
    override fun onCleared() {
        super.onCleared()
        countDownTimer?.cancel()
    }
}

// Game state sealed class
sealed class GameState {
    object Loading : GameState()
    object LoadingLeaderboard : GameState()
    object Timeout : GameState()
    
    data class InProgress(
        val gameId: String,
        val mode: String,
        val options: List<String>,
        val countryName: String? = null,
        val image: Bitmap? = null,
        val timeoutSeconds: Int = 15,
        val timeRemaining: Long = timeoutSeconds.toLong()
    ) : GameState()
    
    data class Completed(
        val isCorrect: Boolean,
        val correctAnswer: String,
        val elapsedTime: Double,
        val countryDetails: CountryDetails
    ) : GameState()
    
    data class Leaderboard(
        val entries: List<LeaderboardEntry>,
        val mode: String
    ) : GameState()
    
    data class Error(val message: String) : GameState()
}

// --- Sample Activity Implementation ---

class GameActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityGameBinding
    private lateinit var viewModel: GameViewModel
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityGameBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        // Initialize ViewModel
        val apiClient = CountryGameApiClient(this)
        val imageLoader = ImageLoader(this)
        val preferencesManager = PreferencesManager(this)
        
        viewModel = ViewModelProvider(this, GameViewModelFactory(
            apiClient, imageLoader, preferencesManager
        )).get(GameViewModel::class.java)
        
        // Get game mode from intent
        val gameMode = intent.getStringExtra("game_mode") ?: "map"
        
        // Set up UI based on game mode
        setupUIForMode(gameMode)
        
        // Observe game state
        viewModel.gameState.observe(this) { state ->
            when (state) {
                is GameState.Loading -> showLoading()
                is GameState.InProgress -> showGameInProgress(state)
                is GameState.Completed -> showGameCompleted(state)
                is GameState.Timeout -> showTimeout()
                is GameState.Leaderboard -> showLeaderboard(state)
                is GameState.LoadingLeaderboard -> showLoadingLeaderboard()
                is GameState.Error -> showError(state.message)
            }
        }
        
        // Start a new game
        viewModel.startGame(gameMode)
    }
    
    // UI setup and state handlers would be implemented here
    
    // Example of setting up option buttons
    private fun setupOptionButtons(options: List<String>) {
        binding.optionsContainer.removeAllViews()
        
        for (option in options) {
            val button = KidFriendlyButton(this).apply {
                text = option
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    resources.getDimensionPixelSize(R.dimen.option_button_height)
                ).apply {
                    setMargins(0, 16, 0, 16)
                }
                
                setOnClickListener {
                    viewModel.submitAnswer(option)
                }
            }
            
            binding.optionsContainer.addView(button)
        }
    }
}
