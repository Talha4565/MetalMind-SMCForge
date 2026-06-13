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
