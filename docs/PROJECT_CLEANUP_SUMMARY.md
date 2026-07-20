# ML-Signals Project Cleanup Summary

## Overview
Comprehensive cleanup and reorganization of the `ml-signals` project workspace to remove legacy frontend files, unrelated documentation, and redundant artifacts while preserving all active project code.

---

## Active Project Structure (Root Level)

### Core Configuration Files
- `.env` - Environment configuration (keep)
- `.env.example` - Example environment template (keep)
- `.gitignore` - Git ignore rules (keep)
- `docker-compose.yml` - Docker Compose configuration (keep)
- `start_all.bat` - Startup script for backend/frontend services (keep)

### Active Project Directories

#### **Python ML/ETL Code**
- `airflow/` - Airflow DAGs for scheduling
- `backtesting/` - Backtesting engine for trading models
- `config/` - Configuration module (references Gold/Silver datasets)
- `data/` - Data handling and feature engineering
- `etl/` - ETL pipeline for data extraction/transformation
- `explainability/` - SHAP analysis for model interpretation
- `features/` - Feature engineering and multi-timeframe analysis
- `models/` - Model training and optimization
- `scripts/` - Utility scripts (e.g., download_silver_data.py)
- `src/` - Core project utilities

#### **API & Frontend Service**
- `api/` - Flask REST API server with CORS configured for localhost:5000
- `frontend/` - Active UI assets (served from `api/app/public/`)
- `instance/` - Flask instance folder for session/config data

#### **Project Data & Model Artifacts**
- `Gold Dataset/` - Raw historical gold price data (OHLC candles)
  - Gold_15m_Candlestick.csv
  - Gold_1h_Candlestick.csv
  - Gold_30m_Candlestick.csv
  - Gold_5m_Candlestick.csv
- `Silver Dataset/` - Raw historical silver price data (OHLC candles)
  - Silver_15m_Candlestick.csv
  - Silver_1h_Candlestick.csv
  - Silver_30m_Candlestick.csv
  - Silver_5m_Candlestick.csv
- `gpp_model.pkl` - Trained Gold Price Prediction model (active reference)
- `xau_ny_london_15m.pkl` - Trained XAU/USD 15m timeframe model (active reference)

#### **Project Outputs**
- `logs/` - Application logs (referenced in active code)
- `reports/` - Backtesting and analysis reports (referenced in active code)

#### **Test Suite**
- `tests/` - Unit and integration tests

### Active Project Scripts
- `run.py` - Main project runner
- `run_etl.py` - ETL pipeline runner
- `run_etl_demo.py` - Demo ETL run with Gold/Silver datasets

---

## Archived Content (`miscellaneous_archive/`)

### Removed from Root & Consolidated

#### **Documentation/** (Non-Project Documents)
- `FIXES_LOG.md` - Historical fix logs
- `FULL_AUDIT_REPORT.md` - Audit/testing reports
- `REACT_VITE_FILES_TO_REMOVE.md` - Inventory of removed React/Vite files
- `V4.txt`, `V5.txt` - Legacy HTML builds (not used)
- `FYP_Report/` - Final Year Project report (not used by active code)
- `notebooks/` - Jupyter notebooks (not referenced by active code)
- `Summaries/` - Historical project summary documents

#### **Legacy Frontend/** (Old React/Vite Dev Server)
- `frontend_localhost3000_archive/` - Complete archived React/Vite frontend
  - Includes node_modules/ (~71K files)
  - package.json, pnpm-lock.yaml
  - src/, public/, build configs
  - **Status**: Removed from development pipeline; Flask backend now serves UI from localhost:5000

#### **Artifacts/** (Package/Dependency Files)
- `package-lock.json` - npm lock file (legacy, archived)

#### **Generated/** (Built/Compiled Outputs)
- [Placeholder for build outputs or generated files]

---

## Changes Made

### 1. **Frontend Deactivation**
- ✅ Removed localhost:3000 (Vite dev server) from `start_all.bat`
- ✅ Removed localhost:3000 and localhost:5173 from CORS origins in `api/app/main.py`
- ✅ Archived entire React/Vite frontend project to `miscellaneous_archive/legacy_frontend/`
- **Result**: Flask backend on localhost:5000 serves UI directly; no more dual-port frontend

### 2. **Documentation Cleanup**
- ✅ Moved all non-project documentation to `miscellaneous_archive/documentation/`
- ✅ Moved FYP_Report and notebooks (not referenced by active code) to archive
- **Result**: Root directory now contains only active project files

### 3. **Artifact Consolidation**
- ✅ Moved package-lock.json (npm artifact) to `miscellaneous_archive/artifacts/`
- ✅ Removed duplicate legacy frontend node_modules folder
- **Result**: Clean separation of legacy dependencies

### 4. **Preserved Active References**
- ✅ Gold/Silver datasets remain in root (referenced in config, ETL, demo scripts)
- ✅ Model PKL files remain in root (referenced in training and backtesting code)
- ✅ logs/ and reports/ remain in root (referenced in active code paths)
- **Result**: All necessary data and model artifacts available for runtime

---

## Verification

### Code References Verified (Still Active)
| Item | References | Location |
|------|-----------|----------|
| Gold Dataset | Multiple | `config/settings.py`, `etl/config.py`, `run_etl_demo.py` |
| Silver Dataset | Multiple | `config/settings.py`, `etl/config.py`, `run_etl_demo.py` |
| gpp_model.pkl | Active | `models/train_enhanced.py`, `config/settings.py` |
| xau_ny_london_15m.pkl | Active | `config/settings.py` |
| reports/ | Active | `backtesting/engine.py` |

### Code References Removed
- All localhost:3000 and localhost:5173 references (dev server ports)
- REACT_VITE_FILES_TO_REMOVE.md documentation of removed files

---

## How to Use the Project

### Start Services
```bash
.\start_all.bat
```
- Flask backend: http://localhost:5000
- Flask serves UI directly (no separate Vite dev server)

### Run ETL
```bash
python run_etl.py        # Production ETL with Gold/Silver data
python run_etl_demo.py   # Demo ETL run
```

### Train Models
```bash
python models/train_enhanced.py   # Train XAU models
python models/train_silver_model.py
```

### Backtesting
Models and backtesting engine in `backtesting/` use data from `Gold Dataset/` and `Silver Dataset/`

---

## Archive Structure (If Needed for Recovery)

```
miscellaneous_archive/
├── artifacts/
│   └── package-lock.json
├── documentation/
│   ├── FIXES_LOG.md
│   ├── FULL_AUDIT_REPORT.md
│   ├── REACT_VITE_FILES_TO_REMOVE.md
│   ├── V4.txt
│   ├── V5.txt
│   ├── FYP_Report/
│   ├── notebooks/
│   └── Summaries/
├── legacy_frontend/
│   └── frontend_localhost3000_archive/  (React/Vite app with node_modules)
└── generated/
    └── [Build outputs placeholder]
```

---

## Summary

✅ **Project is clean and ready for production use:**
- Only active code and necessary data/models in root
- Legacy frontend archived (no localhost:3000 references)
- Documentation and artifacts consolidated
- Flask backend serves UI on single port (localhost:5000)
- All code references verified and working
- Git tracking clean (inactive files removed from working directory)

---

**Date Created**: 2026-01-28  
**Status**: ✅ Complete - Project reorganization finished
