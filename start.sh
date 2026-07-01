#!/bin/bash
uvicorn api:app --host 127.0.0.1 --port 8000 &
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
