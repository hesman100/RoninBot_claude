# Android App UI Mockup

## Main Screen

```
┌─────────────────────────────────────────┐
│          Ronin Bot Commander            │
├─────────┬─────────┬─────────────────────┤
│         │         │                     │
│   💰    │   📈    │        🇻🇳         │
│   /c    │   /s    │        /vn         │
│         │         │                     │
├─────────┼─────────┼─────────────────────┤
│         │         │                     │
│   🗺️    │   🏛️    │        🏳️         │
│ /g map  │ /g cap  │      /g flag       │
│         │         │                     │
├─────────┴─────────┼─────────────────────┤
│                   │                     │
│       🏆          │                     │
│      /g lb        │                     │
│                   │                     │
├───────────────────┴─────────────────────┤
│                                         │
│  Response Area                          │
│                                         │
│  BTC price: $50,234.67 (+2.5%)          │
│  ETH price: $2,789.32 (+1.8%)           │
│  SOL price: $103.45 (+4.2%)             │
│                                         │
├─────────────────────────────────────────┤
│  Status: Connected to Telegram          │
└─────────────────────────────────────────┘
```

## Settings Screen

```
┌─────────────────────────────────────────┐
│               Settings                  │
├─────────────────────────────────────────┤
│                                         │
│  Telegram User ID                       │
│  ┌───────────────────────────────────┐  │
│  │ 123456789                         │  │
│  └───────────────────────────────────┘  │
│                                         │
│  [ How to find your Telegram ID? ]      │
│                                         │
├─────────────────────────────────────────┤
│                                         │
│  Theme                                  │
│  ◉ Light   ○ Dark   ○ System           │
│                                         │
├─────────────────────────────────────────┤
│                                         │
│  Notifications                          │
│  [✓] Enable price alerts                │
│  [✓] Enable game reminders              │
│                                         │
├─────────────────────────────────────────┤
│                                         │
│  Display Options                        │
│  [✓] Show cryptocurrency prices         │
│  [✓] Show stock prices                  │
│  [✓] Show Vietnam stock prices          │
│                                         │
├─────────────────────────────────────────┤
│                                         │
│  [ Save Settings ]     [ Cancel ]       │
│                                         │
└─────────────────────────────────────────┘
```

## Command Detail Screen (Crypto)

```
┌─────────────────────────────────────────┐
│          Cryptocurrency Prices          │
├─────────────────────────────────────────┤
│                                         │
│  [ All Default Coins ]                  │
│                                         │
│  Search Specific Coin:                  │
│  ┌───────────────────────────┐ [ Get ]  │
│  │ BTC                       │          │
│  └───────────────────────────┘          │
│                                         │
├─────────────────────────────────────────┤
│                                         │
│  Recent Results:                        │
│                                         │
│  BTC Bitcoin                            │
│  $50,234.67 (+2.5%)                     │
│                                         │
│  ETH Ethereum                           │
│  $2,789.32 (+1.8%)                      │
│                                         │
│  SOL Solana                             │
│  $103.45 (+4.2%)                        │
│                                         │
│  AXS Axie Infinity                      │
│  $5.67 (-0.8%)                          │
│                                         │
│  RON Ronin                              │
│  $1.23 (+5.6%)                          │
│                                         │
├─────────────────────────────────────────┤
│  [ Back to Main Menu ]                  │
└─────────────────────────────────────────┘
```

## Game Selection Screen

```
┌─────────────────────────────────────────┐
│            Country Games                │
├─────────────────────────────────────────┤
│                                         │
│  [ 🗺️ Map Game ]                        │
│  Guess the country from a map           │
│                                         │
│  [ 🏛️ Capital Game ]                    │
│  Name the capital city of a country     │
│                                         │
│  [ 🏳️ Flag Game ]                       │
│  Identify the country from its flag     │
│                                         │
│  [ 🏆 View Leaderboard ]                │
│  See top players across all games       │
│                                         │
├─────────────────────────────────────────┤
│                                         │
│  Your Stats:                            │
│  🗺️ Map Game: 24/30 (80%)               │
│  🏛️ Capital Game: 18/25 (72%)           │
│  🏳️ Flag Game: 31/40 (77.5%)            │
│                                         │
├─────────────────────────────────────────┤
│  [ Back to Main Menu ]                  │
└─────────────────────────────────────────┘
```

## First-Time Setup Screen

```
┌─────────────────────────────────────────┐
│              Welcome!                   │
├─────────────────────────────────────────┤
│                                         │
│  Complete these steps to get started:   │
│                                         │
│  Step 1: Find Your Telegram ID          │
│  ● Open Telegram                        │
│  ● Search for @userinfobot              │
│  ● Send any message to the bot          │
│  ● Copy your ID number                  │
│                                         │
│  [ Open Telegram ]                      │
│                                         │
│  Step 2: Enter Your Telegram ID         │
│  ┌───────────────────────────────────┐  │
│  │                                   │  │
│  └───────────────────────────────────┘  │
│                                         │
│  Step 3: Test Connection                │
│                                         │
│  [ Send Test Command ]                  │
│                                         │
│  Status: Not connected                  │
│                                         │
│  [ Next ]                               │
│                                         │
└─────────────────────────────────────────┘
```

## Material Design Implementation

The actual implementation would use Material Design components for a polished, modern UI:

- Material Cards for command buttons
- Bottom Navigation for accessing different sections
- Floating Action Button for quick actions
- Material Theming for consistent colors and typography
- Animation for transitions between screens

This mockup provides a general layout, but the final design would include proper spacing, typography, and visual hierarchy following Material Design guidelines.
