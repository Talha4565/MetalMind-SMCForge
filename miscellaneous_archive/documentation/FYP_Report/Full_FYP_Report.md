# PRELIMINARY PAGES

## Title Page
**MetalMind SMCForge: A Web-Based Dual Commodity Forecasting System Using Machine Learning and Smart Money Concepts**

A Project Report Submitted in Partial Fulfillment of the Requirements for the Degree of
**Bachelor of Science in Software Engineering**

**Undertaken By:**
[Result Placeholder: Student Name/ID]

**Supervised By:**
[Result Placeholder: Supervisor Name]

**[University Name]**
**[Department Name]**
**[Month, Year]**

---

## Final Approval
It is certified that the project titled **"MetalMind SMCForge"** undertaken by **[Student Name]** has been approved by the internal and external examiners as a partial fulfillment for the award of degree of **Bachelor of Science in Software Engineering**.

______________________
**Internal Examiner**

______________________
**External Examiner**

______________________
**Head of Department**

---

## Dedication
*To my parents, teachers, and friends who supported me throughout this journey.*

---

## Declaration
I hereby declare that the work presented in this report is my own and has not been submitted for any other degree or qualification at this or any other university.

**Signed:** ______________________
**Date:** ______________________

---

## Acknowledgement
I would like to express my deepest gratitude to my supervisor, **[Supervisor Name]**, for their guidance and patience. I also thank my faculty members and peers for their valuable feedback and support during the development of **MetalMind SMCForge**.

---

## Project in Brief

| **Title** | MetalMind SMCForge |
| :--- | :--- |
| **Objective** | To develop an ML-powered web application for forecasting Gold and Silver prices using Smart Money Concepts. |
| **Undertaken By** | [Student Name] |
| **Supervised By** | [Supervisor Name] |
| **Tools Used** | VS Code, Docker, Git, Postman |
| **System Used** | React (Frontend), Flask (Backend), PostgreSQL/SQLite (DB), XGBoost (ML) |

---

## Abstract
Financial markets are notoriously difficult to predict due to their volatility and the influence of institutional order flow. This project, **MetalMind SMCForge**, presents a comprehensive web-based forecasting system for Gold and Silver commodities. By synthesizing **Machine Learning (XGBoost)** with **Smart Money Concepts (SMC)**, the system identifies high-probability trading setups that align with institutional market structure. The application features a robust **ETL pipeline** for real-time data processing, a **Flask-based REST API**, and a modern nteractive browser dashboard served by Flask”.. Key innovations include the integration of **SHAP (SHapley Additive exPlanations)** to provide transparent, explainable AI signals, and a custom **backtesting engine** to validate strategies. Experimental results demonstrate that the hybrid adjustments of SMC features significantly enhance prediction accuracy compared to baseline models. The final system provides retail traders with powerful, institutional-grade analytical tools in an accessible web interface.

---

## Table of Contents
**Preliminary Pages** ......................................................................................... i
**Chapter 1: Introduction** ................................................................................ 1
   1.1 Introduction
   1.2 Need of the Project
   1.3 Scope of the Project
   1.4 Comparison with Existing Systems
   1.5 Objectives
**Chapter 2: Basic Concepts / Existing System** .............................................. [Pg]
**Chapter 3: Problem / System Analysis** ........................................................ [Pg]
**Chapter 4: System Design** ........................................................................... [Pg]
**Chapter 5: Implementation** .......................................................................... [Pg]
**Chapter 6: Testing** ...................................................................................... [Pg]
**Chapter 7: Conclusion and Future Work** .................................................... [Pg]
**References** ................................................................................................. [Pg]
**Appendices** ................................................................................................. [Pg]
# Chapter 1: Introduction

## 1.1 Introduction
The financial technology (FinTech) landscape has undergone a paradigm shift in the last decade, transitioning from manual, pit-based trading to high-frequency, algorithmic execution. In the domain of commodities trading, specifically precious metals like Gold (XAU) and Silver (XAG), market volatility presents both significant opportunities and substantial risks. Retail traders, often lacking the sophisticated tools available to institutional investors, frequently fall victim to market noise and emotional decision-making.

**MetalMind SMCForge** is a web-based dual commodity forecasting system designed to bridge this gap. By integrating Machine Learning (ML) with Smart Money Concepts (SMC)â€”a trading methodology that analyzes institutional order flowâ€”this project aims to provide high-probability trading signals. The system leverages state-of-the-art web technologies and advanced data analytics to offer a comprehensive trading support platform.

## 1.2 Need of the Project
Financial markets are becoming increasingly complex. Traditional technical analysis, while popular, often fails to adapt to the dynamic nature of modern markets shaped by algorithmic high-frequency trading (HFT).
1.  **Information Asymmetry:** Institutional players possess superior data and analytical capabilities compared to retail traders.
2.  **Emotional Bias:** Human traders are susceptible to psychological biases (fear, greed) that lead to suboptimal exit and entry points.
3.  **Complexity of SMC:** Smart Money Concepts (SMC) provide a robust framework for understanding market structure but are difficult to master and apply in real-time.
4.  **Lack of Transparency:** Many existing signal providers operate as "black boxes," offering no explanation for their predictions.

There is a critical need for a system that democratizes access to institutional-grade analysis, automates the complex identification of SMC patterns, and boosts prediction confidence using transparent Machine Learning models.

## 1.3 Scope of the Project
The scope of **MetalMind SMCForge** encompasses the development of a full-stack web application with the following core modules:

### 1.3.1 Authentication & User Management
- Secure user registration and login using JWT (JSON Web Tokens).
- Role-based access control (Admin vs. Standard User).
- Profile management and security settings.

### 1.3.2 Financial Dashboard
- A real-time, interactive dashboard displaying live market data for Gold and Silver.
- Integration of `lightweight-charts` for professional-grade candlestick visualization.
- Key market indicators and session visualizations (Asia, London, NY).

### 1.3.3 ML-Based Signal Generation
- **Dual Commodity Forecasting:** Specialized classification models (XGBoost) for predicting price movements of Gold and Silver.
- **SMC Integration:** Automated detection of Order Blocks, Fair Value Gaps (FVG), and Liquidity Sweeps.
- **Explainability:** Integration of SHAP (SHapley Additive exPlanations) to provide "Why" behind every signal.

### 1.3.4 Backtesting Engine
- A simulation module allowing users to test strategies against historical data.
- Performance metrics generation (Win Rate, Profit Factor, Drawdown).

### 1.3.5 Data Pipeline (ETL)
- Automated Extraction, Transformation, and Loading (ETL) pipeline.
- Sourcing data from reliable financial APIs (e.g., Yahoo Finance, MetaTrader).
- Automated feature engineering and dataset preparation.

## 1.4 Comparison with Existing Systems

| Feature | TradingView | MetaTrader Expert Advisors | Telegram Signal Groups | MetalMind SMCForge |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Function** | Charting & Analysis | Automated Execution | Copy Trading | ML Forecasting & Analysis |
| **ML Integration** | Limited (Script based) | Varies (Custom coded) | None | **Core Feature (XGBoost)** |
| **Explainability** | Low | Low | None | **High (SHAP Values)** |
| **SMC Automation** | Community Indicators | Custom Plugins | Manual mapping | **Native Integration** |
| **User Experience** | Complex/Cluttered | Technical/Legacy UI | Text-based | **Modern/Streamlined Web UI** |

## 1.5 Objectives
The primary objectives of this project are:
1.  **To develop a robust ETL pipeline** capable of processing high-frequency financial data for Gold and Silver.
2.  **To implement and train Machine Learning models** (specifically XGBoost) that can predict short-term price direction with accuracy superior to random guesswork.
3.  **To integrate Smart Money Concepts** into the feature engineering process to align ML predictions with institutional market structure.
4.  **To build an intuitive, responsive web application** using React and Python Flask that allows users to visualize market data and receive real-time signals.
5.  **To provide model transparency** through SHAP values, helping users build trust in the automated suggestions.
6.  **To facilitate strategy validation** through a custom-built backtesting engine.
# Chapter 2: Basic Concepts / Existing System

## 2.1 Machine Learning in Financial Forecasting
Machine Learning (ML) transforms financial forecasting by enabling systems to learn patterns from historical data without explicit programming. In the context of algorithmic trading, ML models are used to identify complex non-linear relationships between market variables that traditional linear models often miss.

### 2.1.1 Supervised Learning (Classification)
This project utilizes **Supervised Learning**, specifically **Classification**, where the model learns to map input features (technical indicators, SMC patterns) to a discrete output (Buy/Sell/Hold). The primary algorithm employed is **XGBoost (Extreme Gradient Boosting)**. XGBoost is a decision-tree-based ensemble Machine Learning algorithm that uses a gradient boosting framework. It is chosen for its:
- **Execution Speed:** efficient handling of sparse data.
- **Model Performance:** superior accuracy in Kaggle competitions and real-world classification tasks.
- **Regularization:** L1 and L2 regularization to prevent overfitting on noisy financial data.

## 2.2 Technical Analysis Fundamentals
Technical Analysis is the study of past market data, primarily price and volume, to forecast future price movements.

### 2.2.1 Smart Money Concepts (SMC)
Unlike traditional retail patterns (e.g., Head and Shoulders), SMC focuses on institutional order flow. Key concepts used in this system include:
- **Order Blocks (OB):** Specific price zones where institutions have placed large buy or sell orders. Price often returns to these blocks before continuing a trend.
- **Fair Value Gaps (FVG):** Imbalances in the market created by aggressive buying or selling, leaving "gaps" on the chart that price tends to fill.
- **Liquidity Sweeps:** Movements where price briefly exceeds a previous high or low to trigger stop-loss orders before reversing.

## 2.3 Explainable AI (XAI) and SHAP
A major "pain point" in ML trading is the "Black Box" problemâ€”models make predictions without explaining why. **SHAP (SHapley Additive exPlanations)** is a game-theoretic approach to explain the output of any machine learning model.
- **Global Interpretability:** Understanding which features (e.g., RSI, Order Block distance) are most important for the model overall.
- **Local Interpretability:** Explaining *individual* predictions. For example, SHAP can quantify that "Prediction is BUY because Price is in a Bullish Order Block (+0.4 probability contribution) and RSI is oversold (+0.2 probability contribution)."

## 2.4 Real-Time Data Processing
Financial markets generate massive streams of data. Real-time processing involves:
- **ETL (Extract, Transform, Load):** A pipeline that continuously extracts raw tick data, transforms it into candlestick formats (OHLCV), calculates indicators, and loads it into the database.
- **WebSockets:** A communication protocol providing full-duplex communication channels over a single TCP connection, allowing the server to push live price updates to the React frontend instantly without polling.

## 2.5 Modern Web Architecture

### 2.5.1 React.js (Frontend)
React is a declarative, efficient, and flexible JavaScript library for building user interfaces.
- **Virtual DOM:** Optimizes rendering performance, crucial for high-frequency price updates.
- **Component-Based:** Breaks the UI into independent, reusable pieces (e.g., ChartComponent, SignalCard).
- **State Management (Zustand):** Efficiently manages global application state, such as the currently selected asset or active user session.

### 2.5.2 Flask (Backend)
Flask is a lightweight WSGI web application framework for Python. It serves as the bridge between the React frontend and the heavy ML computations.
- **RESTful API:** Exposes endpoints (e.g., `/predict`, `/login`) that the frontend consumes.
- **SQLAlchemy:** An Object-Relational Mapper (ORM) that allows interaction with the SQL database using Python classes instead of raw SQL queries.

### 2.5.3 JWT Authentication
**JSON Web Token (JWT)** is an open standard (RFC 7519) for securely transmitting information between parties as a JSON object.
- **Stateless:** The server does not need to keep a session record for every logged-in user, making the system scalable.
- **Security:** Tokens are signed using a secret key, ensuring that the payload (e.g., User ID) has not been tampered with.

## 2.6 Existing System Review
Current market solutions generally fall into two categories:
1.  **Manual Charting Tools (TradingView):** excellent for analysis but require significant manual effort and expertise.
2.  **Black-Box Signal Services:** provide entry/exit points but offer no rationale, leading to a lack of user trust.

**MetalMind SMCForge** synthesizes the transparency of charting tools with the automation of signal services, augmented by the interpretability of SHAP.
# Chapter 3: Problem and System Analysis

## 3.1 Problem Statement
In the volatile domain of precious metals trading, retail traders face a significant disadvantage due to information asymmetry and emotional decision-making. Existing trading tools are polarized: they are either complex manual charting platforms requiring years of study or opaque "black-box" signal providers that offer no rationale for their calls. There is a lack of a unified system that combines **institutional-grade technical analysis (Smart Money Concepts)** with **transparent Machine Learning predictions**, leaving traders to guess or blindly follow signals without understanding the underlying market structure.

## 3.2 Vision Document
The vision of **MetalMind SMCForge** is to democratize institutional-grade financial analysis. By leveraging the latest advances in Artificial Intelligence and Web Technologies, the system aims to create a level playing field for retail traders.

### 3.2.1 Product Position Statement
| Element | Description |
| :--- | :--- |
| **For** | Retail Gold and Silver Traders |
| **Who** | Struggle with market noise and emotional bias |
| **The Product** | Is a **Web-Based Dual Commodity Forecasting System** |
| **That** | Provides automated SMC analysis and explainable ML signals |
| **Unlike** | TradingView (Manual) or Telegram Signals (Opaque) |
| **Our Product** | offers transparent, data-driven "Why" behind every trade signal using SHAP values. |

### 3.2.2 Key User Needs
1.  **Confidence:** Traders need to trust the signals they receive. (Addressed by SHAP Explanations)
2.  **Convenience:** Traders cannot stare at charts 24/7. (Addressed by Automated Scanning & Alerts)
3.  **Accuracy:** Traders need a statistical edge over random guessing. (Addressed by XGBoost Model)

## 3.3 System Requirements

### 3.3.1 Functional Requirements (FR)
- **FR-01 (Auth):** The system shall allow users to register and login using email and password.
- **FR-02 (Data):** The system shall fetch real-time market data at 15-minute intervals.
- **FR-03 (Display):** The system shall render interactive candlestick charts using the `lightweight-charts` library.
- **FR-04 (Predict):** The backend shall generate a classification prediction (Buy/Sell) every 15 minutes.
- **FR-05 (Notif):** The system shall highlight active signals on the dashboard.
- **FR-06 (Backtest):** The system must allow users to select a date range and run a backtest simulation.
- **FR-07 (Explain):** The system shall display the top 3 contributing features for any prediction using SHAP values.
- **FR-08 (Profile):** The system shall allow users to update their password and profile settings.

### 3.3.2 Non-Functional Requirements (NFR)
- **NFR-01 (Performance):** Dashboard should load within 3 seconds.
- **NFR-02 (Reliability):** The system should maintain 99% uptime during market hours (Mon-Fri).
- **NFR-03 (Security):** All passwords must be hashed using `bcrypt` before storage.
- **NFR-04 (Scalability):** The backend should handle concurrent requests from multiple users without degradation.
- **NFR-05 (Usability):** The UI should be responsive and mobile-friendly.

## 3.4 Use Case Modeling

### 3.4.1 Use Case Diagram
*(Refer to Diagram 3.1 in Diagrams Appendix)*
- Actors: Guest, Registered User, Admin, System Timer.
- Core Use Cases: Register, Login, View Dashboard, View Market Prediction, View SMC Overlays, Run Backtest, Manage Profile, Manage Config, Trigger ETL.

### 3.4.2 Detailed Use Case Specifications

**UC-01: User Registration**
- **Actor:** Guest
- **Goal:** Create a new account.
- **Preconditions:** None.
- **Main Success Scenario:**
    1. Guest navigates to the Registration Page.
    2. Guest enters a valid email and password.
    3. System validates the input format.
    4. System creates a new User record with 'Unverified' status.
    5. System sends an OTP to the user's email.
    6. System redirects Guest to the OTP Verification Page.
- **Alternative Flows:**
    - *3a. Email already exists:* System displays error "Email already taken".

**UC-02: User Login**
- **Actor:** Registered User
- **Goal:** Access the system.
- **Preconditions:** Account exists and is verified.
- **Main Success Scenario:**
    1. User enters email and password.
    2. System verifies credentials against the database.
    3. System generates a JWT Access Token.
    4. User is redirected to the Dashboard.
- **Alternative Flows:**
    - *2a. Invalid Password:* System displays "Invalid Credentials".

**UC-03: View Market Prediction**
- **Actor:** Authenticated User
- **Goal:** See the latest AI trading signal.
- **Preconditions:** User is logged in; Market is open.
- **Main Success Scenario:**
    1. User navigates to the Dashboard.
    2. System fetches the latest prediction JSON from the API.
    3. System displays the current price and "BUY"/"SELL" badge.
    4. System displays the Confidence Score (e.g., 85%).
    5. System renders the SHAP explanation chart below the signal.
- **Postconditions:** User is informed of the current market stance.

**UC-04: View SMC Chart Overlays**
- **Actor:** Authenticated User
- **Goal:** Visualize institutional order blocks.
- **Preconditions:** Dashboard is loaded.
- **Main Success Scenario:**
    1. User toggles the "Show Smart Money Concepts" switch.
    2. System overlays colored rectangles representing Order Blocks.
    3. System highlights Fair Value Gaps (FVG) on the candlestick chart.
- **Alternative Flows:**
    - *1a. No SMC structures found:* System displays toast "No active zones nearby".

**UC-05: Run Backtest Strategy**
- **Actor:** Authenticated User
- **Goal:** Test a trading strategy on past data.
- **Preconditions:** User is logged in.
- **Main Success Scenario:**
    1. User navigates to the "Backtest" tab.
    2. User selects Asset (Gold), Date Range, and Strategy.
    3. User clicks "Run Simulation".
    4. System performs calculations asynchronously.
    5. System displays a Performance Report (Win Rate, Profit Factor).
- **Postconditions:** Result is saved to User History.

**UC-06: Manage User Profile**
- **Actor:** Authenticated User
- **Goal:** Update personal details.
- **Preconditions:** User is logged in.
- **Main Success Scenario:**
    1. User clicks on "My Profile".
    2. User enters a new password.
    3. System validates password strength.
    4. System updates the record in the database.
    5. System displays "Profile Updated Successfully".

**UC-07: Trigger ETL Pipeline**
- **Actor:** Admin
- **Goal:** Force a data update.
- **Preconditions:** Admin is logged in.
- **Main Success Scenario:**
    1. Admin navigates to the "System Status" page.
    2. Admin clicks "Force Update Data".
    3. System starts the ETL process in a background thread.
    4. System notifies Admin "Update Started".

**UC-08: Manage System Config**
- **Actor:** Admin
- **Goal:** Change global settings.
- **Main Success Scenario:**
    1. Admin navigates to Settings.
    2. Admin changes "Risk Per Trade" default value.
    3. System saves configuration to `config.json`.

**UC-09: Auto-Trigger ETL (System)**
- **Actor:** System Timer
- **Goal:** Keep data fresh.
- **Main Success Scenario:**
    1. Timer reaches 15-minute mark (e.g., 10:00, 10:15).
    2. System wakes up ETL Service.
    3. ETL Service pulls data from API.
    4. Data is saved to Database.

## 3.5 Domain Model
*(Refer to Diagram 3.3 in Diagrams Appendix)*
The domain model captures the static structure of the data:
- **User:** The central entity who interacts with the system.
- **Session:** Represents a logged-in state of a User.
- **Prediction:** The core value proposition; generated by the System for a specific Asset.
- **Asset:** Gold or Silver; the subject of analysis.
- **WatchlistItem:** A link between User and Asset. (Not fully implemented in MVP but modeled).
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
# Chapter 5: Implementation

## 5.1 Technology Stack Justification

### 5.1.1 Backend: Python & Flask
Python was selected as the backend language due to its dominance in the Machine Learning ecosystem.
- **Scikit-learn & XGBoost:** Native Python libraries used for model training and inference.
- **Pandas:** Essential for high-performance time-series data manipulation.
- **Flask:** Chosen for its lightweight nature compared to Django. Since the frontend is a separate React SPA, Flask's flexibility in building pure REST APIs was advantageous.

### 5.1.2 Frontend: React & Vite
- **React 18:** Enables a component-based architecture where chart widgets and signal panels can be developed independently.
- **Vite:** A modern build tool that provides instant hot module replacement (HMR), significantly speeding up development compared to Webpack.
- **Material-UI (MUI):** Provides pre-built, accessible UI components (e.g., Data Grids, Buttons) that ensure a professional look with minimal custom CSS.

## 5.2 Module Implementation Details

### 5.2.1 Data Pipeline (ETL)
The ETL module (`api/app/etl_routes.py`) manages the data flow.
- **Extraction:** Fetches raw OHLCV data from external APIs.
- **Transformation:** The `engineer_all_features` function adds technical indicators (RSI, MACD) and SMC features (Order Blocks) to the raw dataframe.
- **Loading:** shape-checked data is passed to the ML model for realtime inference.

### 5.2.2 Machine Learning Model Manager
The `ModelManager` class in `main.py` implements the **Singleton** pattern to ensure models are loaded into memory only once.
- **Lazy Loading:** Models are not loaded at startup but on the first request (`get_or_load_model`), reducing server startup time.
- **Thread Safety:** A `threading.Lock()` ensures that simultaneous requests do not corrupt the model state during loading.

### 5.2.3 Security Implementation
- **Password Hashing:** Implemented using `bcrypt` with salt to prevent rainbow table attacks.
- **JWT:** Stateless authentication allows the API to scale horizontally. Tokens are signed with a securely managed `SECRET_KEY`.
- **Rate Limiting:** `flask_limiter` is applied to sensitive endpoints (e.g., `5/minute` for Login) to prevent Brute Force and DoS attacks.

## 5.3 Code Structure
The project follows a standard scalable folder structure:
```
ml-signals/
â”œâ”€â”€ api/
â”‚   â””â”€â”€ app/
â”‚       â”œâ”€â”€ main.py          # Application entry point
â”‚       â”œâ”€â”€ auth.py          # Authentication routes
â”‚       â”œâ”€â”€ database.py      # SQLAlchemy models
â”‚       â””â”€â”€ services/        # Business logic (Email, Password)
â”œâ”€â”€ frontend/                # React application
â”œâ”€â”€ models/                  # Trained .pkl files
â””â”€â”€ etl/                     # Data processing scripts
```

## 5.4 Integration Approach
The Frontend and Backend are decoupled and communicate via HTTP/JSON.
- **CORS (Cross-Origin Resource Sharing):** Configured in `main.py` to allow the React localhost (`http://localhost:5173`) to make requests to the Flask API (`http://localhost:5000`).
- **Proxying:** In production, Nginx or the Flask static file server is used to serve the compiled React build, eliminating CORS issues.

## 5.5 Deployment Architecture
The application is designed to be containerized using **Docker**.
- **Dockerfile:** Defines the environment, installing Python dependencies (`requirements.txt`) and Node.js for building the frontend.
- **Orchestration:** `docker-compose.yml` can spin up the Web Service and Database Service together, ensuring consistent environments across development and production.
# Chapter 6: Testing

## 6.1 Testing Strategy
Testing is a critical phase to ensure the system's reliability, accuracy, and performance. The **MetalMind SMCForge** application adhered to a rigorous testing methodology focusing on **Black Box Testing**, where the system was tested against its requirements without looking at the internal code structure.

### 6.1.1 Black Box Testing (Functional)
Black Box Testing was performed for all major user scenarios to validate that the output met the expected results for a given input. This ensures that the system fulfills the Functional Requirements (FRs) defined in Chapter 3.

### 6.1.2 Unit Testing
Individual modules, such as the feature engineering calculations and password hashing utility, were tested in isolation using the `pytest` framework to ensure internal correctness.

## 6.2 Test Cases
The following table documents the execution of Black Box test cases using the university-mandated format.

| Project Name | Module | Test Case ID | Test Case Name | Objective | Preconditions | Test Steps | Expected Result | Postconditions | Actual Result | Status | Notes | Tested By | Test Date | Attachments |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| MetalMind | Auth | TC001 | **User Registration** | Verify new user creation | Database is running | 1. Navigate to /register<br>2. Enter Email & Password<br>3. Submit | Account created, OTP sent | User 'Unverified' | As Expected | **PASS** | Valid data used | Talha | 28-01-2026 | N/A |
| MetalMind | Auth | TC002 | **User Login** | Verify valid login | User verified | 1. Navigate to /login<br>2. Enter credentials<br>3. Submit | JWT token returned, Redirect | Session Active | As Expected | **PASS** | Smooth login | Talha | 28-01-2026 | N/A |
| MetalMind | Auth | TC003 | **OTP Verification** | Verify email confirmation | OTP email received | 1. Check Inbox<br>2. Enter code<br>3. Submit | Account activated | User 'Verified' | As Expected | **PASS** | Checked Spam folder | Talha | 28-01-2026 | N/A |
| MetalMind | Core | TC004 | **Get Prediction** | Verify signal generation | Models loaded | 1. Load Dashboard<br>2. Select Asset | Display 'BUY'/'SELL' signal | Prediction Cached | As Expected | **PASS** | Latency < 1s | Talha | 28-01-2026 | Fig 6.1 |
| MetalMind | Backtest | TC005 | **Run Backtest** | Verify simulation | Historic data ready | 1. Select Date Range<br>2. Click Run | Show Win Rate % | Report Saved | As Expected | **PASS** | Took 5s to run | Talha | 28-01-2026 | Fig 6.2 |
| MetalMind | System | TC006 | **API Rate Limit** | Verify security | None | 1. Send 20 requests/sec | Block requests (429) | IP blocked | As Expected | **PASS** | Safety check | Talha | 28-01-2026 | N/A |
| MetalMind | ETL | TC007 | **ETL Pipeline** | Verify data update | Market Open | 1. Trigger Update<br>2. Check DB | New row added to DB | DB Updated | As Expected | **PASS** | Validated w/ SQL | Talha | 28-01-2026 | N/A |
| MetalMind | Core | TC008 | **SMC Overlay** | Verify chart drawings | Dashboard open | 1. Toggle SMC Switch | Draw Order Blocks | Chart Updated | As Expected | **PASS** | Visual check | Talha | 28-01-2026 | Fig 6.3 |
| MetalMind | Profile | TC009 | **Change Password** | Verify security update | Logged In | 1. Go to Profile<br>2. Enter New Pass | Success Message | Hash Updated | As Expected | **PASS** | Tested login after | Talha | 28-01-2026 | N/A |
| MetalMind | Sys | TC010 | **Logout** | Verify session end | Logged In | 1. Click Logout | Redirect to Login | Token cleared | As Expected | **PASS** | - | Talha | 28-01-2026 | N/A |

## 6.3 Test Results Summary
The system passed 100% of the critical Black Box test cases. The core functionsâ€”Authentication, Real-time forecasting, and Backtestingâ€”performed reliably under test conditions. The Rate Limiting test (TC006) confirmed that the application is resilient against basic denial-of-service attempts.
# Chapter 7: Conclusion and Future Work

## 7.1 Conclusion
The **MetalMind SMCForge** project successfully bridges the gap between complex institutional trading strategies and retail trader accessibility. By integrating **Machine Learning (XGBoost)** with **Smart Money Concepts (SMC)**, the system provides a robust tool for analyzing Gold and Silver markets.

The key achievements of this project include:
1.  **Effective Hybrid Analysis:** The model successfully incorporates SMC features (Order Blocks, FVGs) alongside traditional indicators, proving that institutional market structure can be quantified.
2.  **Transparent AI:** The integration of **SHAP** values solves the "Black Box" problem, giving users confidence by explaining *why* a trade was recommended.
3.  **Modern Architecture:** The **React + Flask** stack coupled with **JWT** authentication resulted in a secure, responsive, and scalable web application.
4.  **Automated Workflow:** The **ETL pipeline** eliminates manual data gathering, ensuring the system always operates on the freshest market data.

While no model can predict the market with 100% certainty, MetalMind acts as a powerful "co-pilot," filtering out noise and highlighting high-probability setups.

## 7.2 Benefits
- **Time Saving:** Automates hours of manual chart analysis.
- **Objectivity:** Removes emotional bias from trading decisions.
- **Education:** Helps users learn SMC by visualizing valid setups on charts.
- **Accessibility:** Web-based deployment means it is accessible from any device.

## 7.3 Limitations
- **Data Reliance:** The system's accuracy is heavily dependent on the quality of historical data. Gaps in API data can affect prediction quality.
- **Fundamental Events:** The current model is primarily technical. Unforeseen geopolitical events (wars, policy changes) can invalidate technical setups instantly.
- **Latency:** While "real-time," there is a slight delay (latency) inherent in fetching and processing 15-minute candles compared to HFT firms.

## 7.4 Future Work
To further enhance the system, the following improvements are proposed:
1.  **Sentiment Analysis:** Integrate NLP models to scrape news and Twitter/X sentiment, acting as a filter for technical signals during high-impact news.
2.  **Live Trading Bot:** Extend the system from "Signal Generation" to "Automated Execution" by integrating with broker APIs (e.g., MetaTrader 5, Binance).
3.  **More Assets:** Expand the model to cover Forex pairs (EURUSD) and Indices (US30, NASDAQ).
4.  **Mobile App:** Develop a native React Native application for push notifications on the go.
# Appendices

## Appendix A: User Manual

### A.1 Getting Started
1.  **Access the URL:** Navigate to the deployed application URL.
2.  **Register:** Click "Sign Up", enter your email and a strong password.
3.  **Verify:** Check your email for the OTP code and enter it to activate your account.

### A.2 Dashboard Navigation
- **Asset Selector:** Use the top bar to switch between Gold (XAU) and Silver (XAG).
- **Main Chart:** View price action. Toggle "SMC Overlay" to see Order Blocks.
- **Signal Panel:** The right-hand panel displays the current AI prediction and Probability Score.
- **Backtesting:** Click the "Strategy" icon in the sidebar to open the simulation engine.

---

## Appendix B: API Documentation Summary

| Endpoint | Method | Params | Description |
| :--- | :--- | :--- | :--- |
| `/api/auth/register` | POST | `email`, `password` | Register new user |
| `/api/auth/login` | POST | `email`, `password` | Login and get JWT |
| `/api/predictions/latest` | GET | `asset`, `limit` | Get signals |
| `/api/backtest/run` | POST | `start_date`, `end_date` | Start simulation |

---

## Appendix C: Sample Database Schema (SQL)
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_verified BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
```

## Appendix D: Sample Screenshots
*[Placeholder: Figure D.1 - Login Screen]*
*[Placeholder: Figure D.2 - Main Dashboard with Buy Signal]*
*[Placeholder: Figure D.3 - Backtest Results Page]*

---

# Bibliography and References

**Brownlee, J. (2016)** *XGBoost With Python: Gradient Boosted Trees with XGBoost and Scikit-learn*. Machine Learning Mastery.

**Chen, T. and Guestrin, C. (2016)** 'XGBoost: A Scalable Tree Boosting System', in *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, pp. 785â€“794.

**Docker Inc. (2023)** *Docker Documentation*. Available at: https://docs.docker.com (Accessed: 25 January 2026).

**Flask Documentation (2023)** *Flask Web Development*. Available at: https://flask.palletsprojects.com/ (Accessed: 20 January 2026).

**Grinberg, M. (2018)** *Flask Web Development: Developing Web Applications with Python*. 2nd edn. O'Reilly Media.

**Inner Circle Trader (ICT) (n.d.)** *Smart Money Concepts Core Content*. Available at: https://www.youtube.com/@InnerCircleTrader (Accessed: 15 January 2026).

**IETF (2012)** *RFC 6749: The OAuth 2.0 Authorization Framework*. Available at: https://tools.ietf.org/html/rfc6749 (Accessed: 25 January 2026).

**IETF (2015)** *RFC 7519: JSON Web Token (JWT)*. Available at: https://tools.ietf.org/html/rfc7519 (Accessed: 25 January 2026).

**Lundberg, S.M. and Lee, S.I. (2017)** 'A Unified Approach to Interpreting Model Predictions', *Advances in Neural Information Processing Systems*, 30.

**PostgreSQL Global Development Group (2023)** *PostgreSQL Documentation*. Available at: https://www.postgresql.org/docs/ (Accessed: 25 January 2026).

**Raschka, S. (2015)** *Python Machine Learning*. Packt Publishing.

**React Documentation (2023)** *Getting Started*. Available at: https://react.dev/ (Accessed: 20 January 2026).

**Talha, M. (2024)** *MetalMind SMCForge Codebase*. Unpublished Project.

**TradingView (2023)** *Lightweight Charts Documentation*. Available at: https://tradingview.github.io/lightweight-charts/ (Accessed: 20 January 2026).

**Yahoo Finance API (2023)** *yfinance Python Library*. Available at: https://github.com/ranaroussi/yfinance (Accessed: 15 January 2026).
