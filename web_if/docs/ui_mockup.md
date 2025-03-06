# Web Interface UI Mockup

This document provides a visual representation and description of the user interface for the web version of the country guessing game.

## Main Page (index.html)

```
+------------------------------------------------+
|                                                |
|             COUNTRY GUESSING GAME              |
|                 (Logo/Header)                  |
|                                                |
+------------------------------------------------+
|                                                |
|    +------------+    +------------+            |
|    |    HELP    |    | LEADERBOARD|            |
|    +------------+    +------------+            |
|                                                |
|    +------------+    +------------+            |
|    | GAME MAP   |    | GAME FLAG  |            |
|    +------------+    +------------+            |
|                                                |
|    +------------+                              |
|    | GAME CAP   |                              |
|    +------------+                              |
|                                                |
|    +------------------+  +------------------+  |
|    |  PLAY AS GUEST   |  | CONNECT WALLET   |  |
|    +------------------+  +------------------+  |
|                                                |
|                                                |
|         Bot Version: 1.3                       |
|                                                |
+------------------------------------------------+
```

## Game Screen (game.html)

```
+------------------------------------------------+
|                                                |
|             COUNTRY GUESSING GAME              |
|              MAP MODE (or FLAG/CAP)            |
|                                                |
+------------------------------------------------+
|                                                |
|                                                |
|                                                |
|          [IMAGE OF MAP/FLAG DISPLAYED]         |
|                                                |
|                                                |
|          Which country is this?                |
|          (Timer: 30s)                          |
|                                                |
+------------------------------------------------+
|                                                |
|    +------------+    +------------+            |
|    | Country 1  |    | Country 2  |            |
|    +------------+    +------------+            |
|                                                |
|    +------------+    +------------+            |
|    | Country 3  |    | Country 4  |            |
|    +------------+    +------------+            |
|                                                |
|    +------------+    +------------+            |
|    | Country 5  |    | Country 6  |            |
|    +------------+    +------------+            |
|                                                |
+------------------------------------------------+
```

## Result Screen

```
+------------------------------------------------+
|                                                |
|             COUNTRY GUESSING GAME              |
|                  GAME RESULT                   |
|                                                |
+------------------------------------------------+
|                                                |
|    ✅ Correct! (or ❌ Wrong!)                  |
|                                                |
|    🏳️ Country: Vietnam                        |
|    🏙️ Capital: Hanoi                          |
|    🌍 Region: Asia                             |
|    👥 Population: 97 million                   |
|    📏 Area: 331,212 km²                       |
|                                                |
|                                                |
+------------------------------------------------+
|                                                |
|    +------------+    +------------+            |
|    | PLAY AGAIN |    | NEW GAME   |            |
|    +------------+    +------------+            |
|                                                |
|    +------------+                              |
|    |    MENU    |                              |
|    +------------+                              |
|                                                |
|         Bot Version: 1.3                       |
|                                                |
+------------------------------------------------+
```

## Leaderboard Screen (leaderboard.html)

```
+------------------------------------------------+
|                                                |
|             COUNTRY GUESSING GAME              |
|                  LEADERBOARD                   |
|                                                |
+------------------------------------------------+
|                                                |
|    RANK  USER           SCORE   ACCURACY       |
|    -----------------------------------         |
|    1.    Player123      2500    95%            |
|    2.    GeoExpert      2200    92%            |
|    3.    MapMaster      2000    88%            |
|    4.    Traveler55     1800    85%            |
|    5.    WorldExplorer  1650    82%            |
|    ...                                         |
|                                                |
|                                                |
+------------------------------------------------+
|                                                |
|    +------------+     +------------+           |
|    |    MENU    |     | PLAY GAME  |           |
|    +------------+     +------------+           |
|                                                |
|         Bot Version: 1.3                       |
|                                                |
+------------------------------------------------+
```

## Help Screen (help.html)

```
+------------------------------------------------+
|                                                |
|             COUNTRY GUESSING GAME              |
|                     HELP                       |
|                                                |
+------------------------------------------------+
|                                                |
|    GAME MODES:                                 |
|                                                |
|    • MAP - Guess the country from its map      |
|    • FLAG - Guess the country from its flag    |
|    • CAP - Guess the capital city              |
|                                                |
|    HOW TO PLAY:                                |
|    1. Select a game mode                       |
|    2. You have 30 seconds to answer           |
|    3. Choose from multiple options             |
|                                                |
|    PLAYING AS GUEST:                           |
|    • Play without saving scores                |
|                                                |
|    CONNECT WALLET:                             |
|    • Connect your Ronin wallet to save scores  |
|    • Your results will appear on leaderboard   |
|                                                |
+------------------------------------------------+
|                                                |
|    +------------+                              |
|    |    MENU    |                              |
|    +------------+                              |
|                                                |
|         Bot Version: 1.3                       |
|                                                |
+------------------------------------------------+
```

## Wallet Connection Screen (future implementation)

```
+------------------------------------------------+
|                                                |
|             COUNTRY GUESSING GAME              |
|                CONNECT WALLET                  |
|                                                |
+------------------------------------------------+
|                                                |
|    Connect your Ronin wallet to save your      |
|    game scores and compete on the leaderboard. |
|                                                |
|    +-----------------------------------+       |
|    |          CONNECT RONIN            |       |
|    +-----------------------------------+       |
|                                                |
|    [QR Code or connection interface            |
|     will appear here]                          |
|                                                |
|                                                |
|                                                |
+------------------------------------------------+
|                                                |
|    +------------+                              |
|    |    MENU    |                              |
|    +------------+                              |
|                                                |
|         Bot Version: 1.3                       |
|                                                |
+------------------------------------------------+
```

## Mobile Responsive Design

The web interface will be responsive and adapt to mobile screen sizes, with a similar layout but optimized for touch interaction and smaller screens.

## Visual Theme

The interface will use a clean, modern design with:
- A world map or globe background theme
- Blue and green color palette representing Earth
- Clear, high-contrast buttons for easy interaction
- Consistent display of game version information
- Simple animations for game transitions and results
