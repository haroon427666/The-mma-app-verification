/** HTTP Status codes + Network errors reference */
export const HttpStatus = {
  OK: 200, CREATED: 201, NO_CONTENT: 204, NOT_MODIFIED: 304,
  BAD_REQUEST: 400, UNAUTHORIZED: 401, FORBIDDEN: 403, NOT_FOUND: 404,
  CONFLICT: 409, UNPROCESSABLE: 422, RATE_LIMITED: 429,
  SERVER_ERROR: 500, BAD_GATEWAY: 502, SERVICE_UNAVAILABLE: 503, GATEWAY_TIMEOUT: 504,
} as const;

export const NetworkErrorMessages = {
  OFFLINE: 'No network connection', TIMEOUT: 'Request timed out',
  RATE_LIMITED: 'Too many requests', UNAUTHORIZED: 'Authentication required',
  SERVER_ERROR: 'Server error occurred', UNKNOWN: 'An unexpected error occurred',
} as const;
