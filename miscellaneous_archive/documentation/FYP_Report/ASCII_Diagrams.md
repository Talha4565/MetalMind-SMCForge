# FYP Report Diagrams (ASCII / Stick Pattern)

## Chapter 3: Use Case Diagram

```text
      Guest                  System                  Admin
        o                                              o
       /|\                                            /|\
       / \                                            / \
        |                                              |
        |          +------------------------+          |
        +--------->|      Register (UC1)    |          |
        |          +------------------------+          |
        |                                              |
        |          +------------------------+          |
        +--------->|       Login (UC2)      |<---------+
                   +------------------------+          |
        o                                              |
       /|\         +------------------------+          |
       / \ +------>|    View Dashboard      |          |
        |          +------------------------+          |
      User                                             |
        |          +------------------------+          |
        +--------->|  View Prediction/Signal|          |
        |          +------------------------+          |
        |                                              |
        |          +------------------------+          |
        +--------->|    Run Backtest (UC6)  |<---------+
        |          +------------------------+          |
        |                                              |
        |          +------------------------+          |
        |          |   Trigger ETL Pipeline |<---------+
        |          +------------------------+          |
        |                                              |
        |          +------------------------+          |
        |          |  Manage System Config  |<---------+
                   +------------------------+
```

## Chapter 3: System Sequence Diagram (Get Prediction)

```text
User                 Frontend                  API
 o                      |                       |
/|\                     |                       |
/ \   1. Refresh        |                       |
 | -------------------> |                       |
 |                      |  2. GET /predict      |
 |                      | --------------------> |
 |                      |                       |
 |                      |                       |----.
 |                      |                       |    | 3. Check Auth
 |                      |                       |<---'
 |                      |                       |
 |                      |   4. JSON Response    |
 |                      | <-------------------- |
 |    5. Update UI      |                       |
 | <------------------- |                       |
```

## Chapter 4: System Architecture Diagram

```text
+---------------------+          +------------------------------------------+
|     Client Side     |          |               Server Side                |
|                     |          |                                          |
|  +---------------+  |   HTTP   |  +-------------+       +--------------+  |
|  |               |  |   JSON   |  |             |       |              |  |
|  | React Frontend|<-+--------->+->|  Flask API  +------>| Model Manager|  |
|  |               |  |          |  |             |       |              |  |
|  +---------------+  |          |  +------+------+       +-------+------+  |
|                     |          |         |                      |         |
+---------------------+          |         v                      v         |
                                 |  +-------------+       +--------------+  |
                                 |  |             |       |              |  |
                                 |  |  Database   |       |  ML Models   |  |
                                 |  | (SQLite/PG) |       |    (.pkl)    |  |
                                 |  |             |       |              |  |
                                 |  +-------------+       +--------------+  |
                                 +------------------------------------------+
```

## Chapter 4: Entity Relationship Diagram (ERD)

```text
       +------------------+                  +------------------+
       |      USERS       | 1              N |     SESSIONS     |
       +------------------+------------------+------------------+
       | PK id            |                  | PK id            |
       |    email         |                  |    session_id    |
       |    password_hash |                  | FK user_id       |
       |    is_verified   |                  |    ip_address    |
       +------------------+                  +------------------+
                | 1
                |
                | N
       +------------------+
       | WATCHLIST_ITEMS  |
       +------------------+
       | PK id            |
       | FK user_id       |
       |    symbol        |
       |    alert         |
       +------------------+
```

## Chapter 4: Activity Diagram (Prediction Flow)

```text
      (Start)
         |
         v
  [15m Timer Triggers]
         |
         v
  [ Fetch OHLCV Data ]
         |
         v
   < Is Data Valid? >----No-----> (Log Error & Stop)
         | Yes
         v
  [ Calculate Indicators ]
         |
         v
  [  Calculate SMC / FVG ]
         |
         v
  [   Load XGBoost Model ]
         |
         v
  [  Generate Prediction ]
         |
         v
  [   Update WebSockets  ]
         |
         v
       (End)
```
