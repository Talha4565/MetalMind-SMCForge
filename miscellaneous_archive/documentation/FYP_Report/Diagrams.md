# FYP Report Diagrams

This document contains the source code for all required diagrams in Mermaid.js format. You can render these using any Markdown editor that supports Mermaid (like VS Code, Obsidian, or GitHub) or use an online live editor (https://mermaid.live).

## Chapter 3: Use Case Diagram

```mermaid
usecaseDiagram
    actor "Guest User" as Guest
    actor "Registered User" as User
    actor "Admin" as Admin
    actor "System Timer" as Timer

    package "MetalMind SMCForge" {
        usecase "Register" as UC1
        usecase "Login" as UC2
        usecase "View Dashboard" as UC3
        usecase "View Market Prediction" as UC4
        usecase "View SMC Overlays" as UC5
        usecase "Run Backtest" as UC6
        usecase "Manage User Profile" as UC7
        usecase "Trigger ETL Pipeline" as UC8
        usecase "Manage System Config" as UC9
    }

    Guest --> UC1
    Guest --> UC2
    
    User --> UC2
    User --> UC3
    User --> UC4
    User --> UC5
    User --> UC6
    User --> UC7
    
    Admin --> UC8
    Admin --> UC9
    Admin --> UC6
    
    Timer --> UC8
```

## Chapter 3: System Sequence Diagram (Get Prediction)

```mermaid
sequenceDiagram
    actor User
    participant Frontend as React App
    participant API as Flask API

    User->>Frontend: Click "Refresh Predictions"
    Frontend->>API: GET /api/predictions/latest?asset=gold
    activate API
    API-->>API: Check Rate Limit & Auth
    API-->>Frontend: Return JSON (Prices + Signal + Probability)
    deactivate API
    Frontend-->>User: Update Chart & Signal Panel
```

## Chapter 3: Domain Model

```mermaid
classDiagram
    direction LR
    class User {
        email
        password_hash
        is_verified
    }
    class Session {
        session_id
        ip_address
        expires_at
    }
    class WatchlistItem {
        symbol
        alert_threshold
    }
    class Prediction {
        timestamp
        asset
        direction
        probability
    }
    class MarketData {
        open
        high
        low
        close
        volume
    }

    User "1" -- "0..*" Session : has
    User "1" -- "0..*" WatchlistItem : monitors
    WatchlistItem "1" -- "1" MarketData : tracks
    MarketData "1" -- "0..*" Prediction : generates
```

## Chapter 4: System Architecture Diagram

```mermaid
graph TD
    subgraph Client_Side [Client Side]
        Browser[Web Browser]
        React[React Application]
    end

    subgraph Server_Side [Server Side]
        API[Flask REST API]
        Auth[Auth Service]
        ETL[ETL Pipeline]
        ModelMgr[Model Manager]
    end

    subgraph Data_Layer [Data Layer]
        DB[(SQLite/Postgres)]
        Models[ML Models (.pkl)]
        Cache[File Cache]
    end

    subgraph External [External Services]
        YF[Yahoo Finance API]
    end

    Browser -->|HTTP/WebSocket| React
    React -->|JSON Requests| API
    
    API --> Auth
    API --> ModelMgr
    API --> DB
    
    ModelMgr --> Models
    ModelMgr --> Cache
    
    ETL -->|Schedule| YF
    ETL -->|Store| DB
    ETL -->|Update| Cache
```

## Chapter 4: Interaction (Sequence) Diagram - detailed

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Dashboard (React)
    participant API as Flask Server
    participant DB as Database
    participant MM as ModelManager
    
    User->>UI: Selects "Gold" Asset
    UI->>API: GET /api/predictions/latest?asset=gold
    activate API
    
    API->>API: Verify JWT Token
    
    API->>MM: get_or_load_model("gold")
    activate MM
    alt Model Cached
        MM-->>API: Return Model Object
    else Model Not Loaded
        MM->>MM: Load .pkl from disk
        MM-->>API: Return Model Object
    end
    deactivate MM
    
    API->>DB: Fetch Latest OHLCV Data
    activate DB
    DB-->>API: Return Data Rows
    deactivate DB
    
    API->>API: Generate Feature Set (SMC + Indicators)
    API->>API: Run Inference (model.predict)
    
    API-->>UI: Return JSON {signal: 1, prob: 0.85}
    deactivate API
    
    UI->>User: Display "BUY" Signal
```

## Chapter 4: Class Diagram (Backend)

```mermaid
classDiagram
    class ModelManager {
        -models: dict
        -lock: Lock
        +get_or_load_model(asset)
        +load_model(asset)
    }

    class PredictionCache {
        -cache: dict
        -ttl: int
        +get(key)
        +set(key, value)
    }

    class BacktestManager {
        -status: dict
        -lock: Lock
        +run(start_date, end_date)
        +get_status()
    }

    class ETLConfig {
        +schedule_interval: int
        +api_source: str
    }

    class Pipeline {
        +run()
        +transform()
        +load()
    }

    ModelManager ..> PredictionCache : uses
    Pipeline --|> ETLConfig : configured by
```

## Chapter 4: Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    USERS ||--o{ SESSIONS : "logs in"
    USERS ||--o{ OTP_CODES : "receives"
    USERS ||--o{ WATCHLIST_ITEMS : "tracks"
    
    USERS {
        int id PK
        string email
        string password_hash
        boolean is_verified
        boolean totp_enabled
    }

    SESSIONS {
        int id PK
        string session_id
        int user_id FK
        datetime expires_at
    }

    OTP_CODES {
        int id PK
        string code
        int user_id FK
        boolean is_used
    }

    WATCHLIST_ITEMS {
        int id PK
        string symbol
        float alert_threshold
        int user_id FK
    }
```

## Chapter 4: Activity Diagram (ETL Process)

```mermaid
flowchart TD
    Start((Start)) --> Trigger[Timer Trigger (15m)]
    Trigger --> FetchData[Fetch Data from API]
    
    FetchData --> CheckErrors{Data Valid?}
    CheckErrors -- No --> LogError[Log Error] --> End((Stop))
    CheckErrors -- Yes --> Process[Process OHLCV]
    
    Process --> CalcInd[Calculate Generic Indicators]
    CalcInd --> CalcSMC[Calculate SMC Features]
    CalcSMC --> Engineer[Engineer ML Features]
    
    Engineer --> Store[Store in Database]
    Store --> LoadModel[Load XGBoost Model]
    LoadModel --> Predict[Generate Prediction]
    
    Predict --> Cache[Update JSON Cache]
    Cache --> Notify[Notify WebSocket Clients]
    Notify --> End
```
