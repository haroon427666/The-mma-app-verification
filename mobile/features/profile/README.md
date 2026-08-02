# Profile Feature

## API Endpoints
- `GET /v1/me`
- `GET /v1/me/sessions`

## State Ownership
- Global `authStore`: user data, tokens, auth status
- `profileStore`: active section for accordion

## Account Actions
- Logout, logout all, delete account (call `authService`)
- Theme switching (calls `useUIStore`)
