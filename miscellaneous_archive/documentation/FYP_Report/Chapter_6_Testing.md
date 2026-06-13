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
The system passed 100% of the critical Black Box test cases. The core functions—Authentication, Real-time forecasting, and Backtesting—performed reliably under test conditions. The Rate Limiting test (TC006) confirmed that the application is resilient against basic denial-of-service attempts.
