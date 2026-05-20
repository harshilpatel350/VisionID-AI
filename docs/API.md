# VisionID AI API

Base URL: `http://localhost:8000/api`

## Auth

### POST /auth/register
### POST /auth/login
### GET /auth/me

## Health

### GET /health

## Persons

### GET /faces/persons
### POST /faces/persons
### GET /faces/persons/{id}
### PUT /faces/persons/{id}
### DELETE /faces/persons/{id}
### POST /faces/persons/{id}/samples
### POST /faces/search
### GET /faces/duplicates

## Recognition

### POST /recognition/image
### POST /recognition/video
### POST /recognition/batch
### GET /recognition/logs
### WS /ws/recognition

## Dashboard

### GET /dashboard/stats
### GET /analytics/overview

## Admin

### GET /admin/users
### GET /admin/audit-logs

## Export

### GET /exports/recognition.csv
### GET /exports/recognition.xlsx
