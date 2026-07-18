# Sentinel AI - Database Schema Design

Sentinel AI utilizes a MySQL 8.0 relational database to track tenancy, organizations, teams, repositories, scanning metadata, identified secrets, and audit histories.

---

## Entity Relationship (ER) Diagram

```mermaid
erDiagram
    users {
        int id PK
        string email UK
        string hashed_password
        string first_name
        string last_name
        string role
        bool is_active
        bool is_verified
        bool mfa_enabled
        string mfa_secret
        datetime created_at
        datetime updated_at
    }

    organizations {
        int id PK
        string name
        string slug UK
        string billing_status
        datetime created_at
        datetime updated_at
    }

    user_organizations {
        int user_id PK, FK
        int organization_id PK, FK
        string role
        datetime created_at
    }

    teams {
        int id PK
        int organization_id FK
        string name
        datetime created_at
        datetime updated_at
    }

    team_members {
        int team_id PK, FK
        int user_id PK, FK
        string role
        datetime created_at
    }

    projects {
        int id PK
        int organization_id FK
        string name
        string description
        datetime created_at
        datetime updated_at
    }

    repositories {
        int id PK
        int project_id FK
        string name
        string clone_url
        string provider
        bool is_active
        string access_token
        datetime last_synced_at
        datetime created_at
        datetime updated_at
    }

    branches {
        int id PK
        int repository_id FK
        string name
        bool is_default
        datetime created_at
        datetime updated_at
    }

    scans {
        int id PK
        int repository_id FK
        int branch_id FK
        string commit_hash
        string status
        string error_message
        datetime started_at
        datetime finished_at
        int total_files
        int secrets_found
        float risk_score
        datetime created_at
    }

    secrets {
        int id PK
        int scan_id FK
        int repository_id FK
        string file_path
        int line_number
        int column_number
        string secret_type
        string detected_value_hashed
        string masked_value
        float entropy
        string status
        string severity
        text raw_context
        datetime created_at
        datetime updated_at
    }

    audit_logs {
        int id PK
        int user_id FK
        string action
        string ip_address
        string user_agent
        text details
        datetime created_at
    }

    user_sessions {
        int id PK
        int user_id FK
        string refresh_token_hash UK
        datetime expires_at
        datetime created_at
    }

    api_tokens {
        int id PK
        int user_id FK
        string name
        string token_hash UK
        datetime expires_at
        datetime created_at
    }

    users ||--o{ user_organizations : belongs_to
    organizations ||--o{ user_organizations : contains
    organizations ||--o{ teams : owns
    teams ||--o{ team_members : has
    users ||--o{ team_members : joined
    organizations ||--o{ projects : manages
    projects ||--o{ repositories : includes
    repositories ||--o{ branches : tracks
    repositories ||--o{ scans : scanned_in
    branches ||--o{ scans : target_for
    scans ||--o{ secrets : exposes
    repositories ||--o{ secrets : found_in
    users ||--o{ audit_logs : triggers
    users ||--o{ user_sessions : establishes
    users ||--o{ api_tokens : generates
```

---

## Detailed Model Mapping

### 1. `users`
- Stores user credentials, active state, global role (e.g. system `admin` vs standard `member`), and MFA details.
- Hashing utilizes the `Argon2` password hashing scheme.

### 2. `organizations` & `user_organizations`
- Tenancy boundaries. Users can belong to multiple organizations with different organizational roles (`owner`, `member`, `auditor`).
- `slug` is used for front-end subdomains or custom scoping (e.g. `/org/acme-corp`).

### 3. `scans`
- Tracks scanning executions.
- `status` can be `"pending"`, `"running"`, `"completed"`, or `"failed"`.
- `risk_score` is computed automatically on completion from `0` (vulnerable) to `100` (secure).

### 4. `secrets`
- Stores specific leak events.
- **Security Guardrail**: Raw secrets are **never** stored in the database. Instead:
  - `detected_value_hashed`: stores a `SHA-256` hash of the secret string. This allows matching duplicates across different commits/scans without saving cleartext passwords.
  - `masked_value`: stores a secure masked string (e.g. `AKIA...7EXA`) for UI presentation.
  - `raw_context`: stores the matching line with the secret replaced by the masked string.
