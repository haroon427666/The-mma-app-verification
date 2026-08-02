# Rankings Module — Complete Production Rankings Platform

## Architecture
```
Screen → Hook → Repository → API
```

## Features
- P4P rankings with composite scores
- All 11 division rankings with champion banners
- GOAT rankings (Elo peak, defenses, era, finish rate)
- Prospect tracker with trajectory and comparable fighters
- Ranking movement tracker (biggest risers/fallers)
- Champion history with reign duration and defenses
- Title defenses leaderboard
- ELO and composite score leaderboards
- Fighter rank history timeline
- Offline caching with background refresh
- Pin/favorite divisions and fighters

## API Endpoints
See API.md

## Cache Strategy
- Rankings: 10 min stale
- Movement/Streaks: 1 min stale (live data)
- GOAT/Champions: 20 min stale
- History: 10 min stale
