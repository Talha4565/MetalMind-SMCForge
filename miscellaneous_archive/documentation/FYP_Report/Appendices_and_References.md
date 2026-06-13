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

**Chen, T. and Guestrin, C. (2016)** 'XGBoost: A Scalable Tree Boosting System', in *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, pp. 785–794.

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
