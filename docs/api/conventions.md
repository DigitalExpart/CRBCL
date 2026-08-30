# CRBCL API Conventions

## Base URL
`/api/v1`

## Standard Response Envelopes

### Paginated Collections
```json
{
  "items": [ ... ],
  "pagination": {
    "total": 120,
    "limit": 50,
    "offset": 0,
    "has_more": true
  }
}
```

### Error Responses
```json
{
  "error": {
    "code": "CLIENT_NOT_FOUND",
    "message": "Client not found",
    "details": {}
  }
}
```

## HTTP Status Codes
- `200 OK`: Successful retrieval or update
- `201 Created`: Resource successfully created
- `400 Bad Request`: Malformed parameters
- `401 Unauthorized`: Unauthenticated / expired credentials
- `403 Forbidden`: Permission or team scope violation
- `404 Not Found`: Resource does not exist
- `409 Conflict`: Unique constraint violation (e.g. email duplicate)
- `422 Unprocessable Entity`: Pydantic validation failure
- `500 Internal Server Error`: Generic safe message (raw SQL errors never exposed)
