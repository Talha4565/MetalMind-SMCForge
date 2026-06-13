# Chapter 4: System Design

## 4.1 System Architecture
The **MetalMind SMCForge** application follows a **Three-Tier Architecture** consisting of the Presentation Layer (Frontend), Logic Layer (Backend API & ML), and Data Layer (Database). This separation of concerns ensures scalability, maintainability, and ease of testing.

### 4.1.1 Architectural Diagram
*[Placeholder: Figure 4.1 - System Block Diagram]*
- **Client Tier:** React JS Application running in the user's browser.
- **Application Tier:** Python Flask server housing the REST API, Authentication Logic, and ML Model Manager.
- **Data Tier:** SQLite (development) / PostgreSQL (production) for user data, and a file-based cache for ML models (.pkl) and Backtest Reports (.json).

## 4.2 Class Design
The backend is structured using Object-Oriented Programming (OOP) principles. Key classes in the Python backend include:

### 4.2.1 Core Modules (`main.py` & Services)
- **ModelManager:** A thread-safe singleton responsible for lazy-loading ML models (`enhanced_15m.pkl`). methods: `load_model()`, `get_or_load_model()`.
- **PredictionCache:** Manages in-memory caching of prediction results to reduce computation load. Methods: `get()`, `set()`.
- **BacktestManager:** Handles lengthy backtesting processes asynchronously. Methods: `run()`, `get_status()`.

### 4.2.2 Database Models (`database.py`)
- **User:** Represents a registered user. Fields: `id`, `email`, `password_hash`, `is_verified`, `totp_enabled`.
- **Session:** Tracks active user sessions. Fields: `session_id`, `user_id`, `ip_address`, `expires_at`.
- **OTPCode:** Manages One-Time Passwords for email verification. Fields: `code`, `expires_at`, `is_used`.
- **WatchlistItem:** Stores user-selected assets. Fields: `symbol`, `alert_threshold`.

## 4.3 Database Design (ERD)
The Entity-Relationship Diagram (ERD) visualizes the data structure.

*[Placeholder: Figure 4.2 - Entity Relationship Diagram]*
- **One User** can have **Many Sessions** (1:N).
- **One User** can have **Many WatchlistItems** (1:N).
- **One User** can have **Many OTPCodes** (1:N).

## 4.4 API Design
The backend exposes a RESTful API. Key endpoints include:

### 4.4.1 Authentication (`/api/auth`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| POST | `/login` | Authenticates user and returns JWT token. |
| POST | `/register` | Creates a new user account. |
| POST | `/verify-email` | Validates OTP code for account activation. |

### 4.4.2 Predictions & Data (`/api/predictions`, `/api/models`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| GET | `/latest?asset=gold` | Returns latest OHLCV data with Buy/Sell signal. |
| GET | `/info?asset=gold` | Returns model metadata (accuracy, feature count). |

### 4.4.3 ETL & Backtesting (`/api/etl`, `/api/backtest`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| POST | `/backtest/run` | Initiates a historical simulation. |
| GET | `/backtest/results` | Retrieves JSON report of last backtest. |
| GET | `/etl/status` | Checks if the data pipeline is currently running. |

## 4.5 Component Design (Frontend)
The React frontend is modularized into functional components:
- **DashboardLayout:** Main container with Sidebar and Header.
- **ChartContainer:** Wrapper for `lightweight-charts` canvas.
- **SignalCard:** Displays the current prediction (Buy/Sell) and Probability %.
- **SHAPExplainer:** Visualizes feature importance bar charts.
- **BacktestPanel:** Form inputs for date range and strategy selection.

## 4.6 Interaction Diagrams

### 4.6.1 Sequence Diagram: User Login
1. **User** enters credentials on Login Page.
2. **Frontend** sends `POST /api/auth/login` to Backend.
3. **Backend** queries `User` table to find email.
4. **Backend** validates password hash using `bcrypt`.
5. **Backend** creates a new `Session` record.
6. **Backend** returns JWT Access Token.
7. **Frontend** stores token and redirects to Dashboard.

### 4.6.2 Activity Diagram: Prediction Generation
1. **Scheduler** triggers ETL job.
2. **ETL Pipeline** fetches fresh data from API.
3. **Feature Engineer** calculates Indicators + SMC Features.
4. **Model Manager** loads XGBoost model.
5. **Model** generates Prediction (0/1).
6. **System** caches result in `PredictionCache`.
7. **WebSocket** pushes update to connected clients.
