# Sentinel AI - API Documentation

Sentinel AI exposes a versioned REST API under `/api/v1` for managing users, organizations, teams, projects, repositories, scans, secrets, and metrics.

---

## Authentication

All protected endpoints require a JWT Bearer token in the `Authorization` header:

```http
Authorization: Bearer <your_access_token>
```

### 1. Register User
- **Endpoint**: `POST /api/v1/auth/register`
- **Request Body** (`UserCreate`):
  ```json
  {
    "email": "user@example.com",
    "password": "strongPassword123",
    "first_name": "Jane",
    "last_name": "Doe"
  }
  ```
- **Response** (`UserOut`):
  ```json
  {
    "id": 1,
    "email": "user@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "role": "admin",
    "is_active": true,
    "is_verified": false,
    "mfa_enabled": false,
    "created_at": "2026-07-01T00:00:00Z",
    "updated_at": "2026-07-01T00:00:00Z"
  }
  ```

### 2. Login (Get Access Token)
- **Endpoint**: `POST /api/v1/auth/login`
- **Request Body** (Form-Data):
  - `username`: User email
  - `password`: User password
- **Response** (`Token`):
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer"
  }
  ```

### 3. Refresh Access Token
- **Endpoint**: `POST /api/v1/auth/refresh`
- **Query Parameter**:
  - `refresh_token`: The refresh token string
- **Response** (`Token`):
  ```json
  {
    "access_token": "newAccess...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer"
  }
  ```

### 4. Auth0/Google Login & Registration
- **Endpoint**: `POST /api/v1/auth/auth0-login`
- **Request Body** (`Auth0Login`):
  ```json
  {
    "token": "your_auth0_access_token"
  }
  ```
- **Response** (`Token`):
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer"
  }
  ```

---

## Profile Management

### 1. Get My Profile
- **Endpoint**: `GET /api/v1/users/me`
- **Response**: `UserOut`

### 2. Update Profile
- **Endpoint**: `PUT /api/v1/users/me`
- **Request Body** (`UserUpdate`):
  ```json
  {
    "first_name": "NewFirstName",
    "last_name": "NewLastName"
  }
  ```
- **Response**: `UserOut`

---

## Organizations & Teams

### 1. Create Organization
- **Endpoint**: `POST /api/v1/organizations/`
- **Request Body** (`OrgCreate`):
  ```json
  {
    "name": "Acme Corp",
    "slug": "acme-corp"
  }
  ```
- **Response**: `OrgOut`

### 2. Get My Organizations
- **Endpoint**: `GET /api/v1/organizations/`
- **Response**: `List[OrgOut]`

### 3. Get Organization Members
- **Endpoint**: `GET /api/v1/organizations/{org_id}/members`
- **Response**: `List[OrgMemberOut]`

### 4. Create Team in Org
- **Endpoint**: `POST /api/v1/organizations/{org_id}/teams`
- **Request Body** (`TeamCreate`):
  ```json
  {
    "name": "Security Team"
  }
  ```
- **Response**: `TeamOut`

---

## Repository Management & Scans

### 1. Register Repository
- **Endpoint**: `POST /api/v1/repositories/`
- **Request Body** (`RepositoryCreate`):
  ```json
  {
    "project_id": 1,
    "name": "my-web-app",
    "clone_url": "https://github.com/acme/my-web-app.git",
    "provider": "github",
    "access_token": "optional_github_token"
  }
  ```
- **Response**: `RepositoryOut`

### 2. List Repositories
- **Endpoint**: `GET /api/v1/repositories/`
- **Query Parameter**:
  - `project_id`: ID of the project
- **Response**: `List[RepositoryOut]`

### 3. Trigger Scanning
- **Endpoint**: `POST /api/v1/repositories/{repo_id}/scan`
- **Query Parameter**:
  - `branch_name`: branch to scan (defaults to `"main"`)
- **Response** (`ScanOut`):
  ```json
  {
    "id": 1,
    "repository_id": 1,
    "branch_id": 1,
    "commit_hash": null,
    "status": "pending",
    "error_message": null,
    "started_at": null,
    "finished_at": null,
    "total_files": 0,
    "secrets_found": 0,
    "risk_score": 0.0,
    "created_at": "2026-07-01T00:00:00Z"
  }
  ```

---

## Secrets & Vulnerabilities

### 1. List Detected Leaks
- **Endpoint**: `GET /api/v1/secrets/`
- **Query Parameters (Optional)**:
  - `repository_id`: Filter by repository ID
  - `scan_id`: Filter by scan ID
  - `severity`: `"critical"`, `"high"`, `"medium"`, `"low"`
  - `status`: `"active"`, `"resolved"`, `"false_positive"`
- **Response**: `List[SecretOut]`

### 2. Update Secret Status
- **Endpoint**: `PUT /api/v1/secrets/{secret_id}/status`
- **Request Body** (`SecretStatusUpdate`):
  ```json
  {
    "status": "resolved"
  }
  ```
- **Response**: `SecretOut`

---

## Dashboard Analytics

### 1. Summary Statistics
- **Endpoint**: `GET /api/v1/dashboard/stats`
- **Response**:
  ```json
  {
    "total_repositories": 1,
    "total_scans": 3,
    "secrets_found": 5,
    "average_risk_score": 82.5
  }
  ```

### 2. Secrets Breakdown by Severity (Pie Chart data)
- **Endpoint**: `GET /api/v1/dashboard/charts/secrets-by-severity`
- **Response**:
  ```json
  {
    "critical": 1,
    "high": 2,
    "medium": 2,
    "low": 0
  }
  ```

### 3. Secrets Breakdown by Type (Bar Chart data)
- **Endpoint**: `GET /api/v1/dashboard/charts/secrets-by-type`
- **Response**:
  ```json
  {
    "AWS Access Key ID": 1,
    "Stripe API Key": 2,
    "OpenAI API Key": 1,
    "Slack Webhook URL": 1
  }
  ```
