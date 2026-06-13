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
├── api/
│   └── app/
│       ├── main.py          # Application entry point
│       ├── auth.py          # Authentication routes
│       ├── database.py      # SQLAlchemy models
│       └── services/        # Business logic (Email, Password)
├── frontend/                # React application
├── models/                  # Trained .pkl files
└── etl/                     # Data processing scripts
```

## 5.4 Integration Approach
The Frontend and Backend are decoupled and communicate via HTTP/JSON.
- **CORS (Cross-Origin Resource Sharing):** Configured in `main.py` to allow the React localhost (`http://localhost:5173`) to make requests to the Flask API (`http://localhost:5000`).
- **Proxying:** In production, Nginx or the Flask static file server is used to serve the compiled React build, eliminating CORS issues.

## 5.5 Deployment Architecture
The application is designed to be containerized using **Docker**.
- **Dockerfile:** Defines the environment, installing Python dependencies (`requirements.txt`) and Node.js for building the frontend.
- **Orchestration:** `docker-compose.yml` can spin up the Web Service and Database Service together, ensuring consistent environments across development and production.
