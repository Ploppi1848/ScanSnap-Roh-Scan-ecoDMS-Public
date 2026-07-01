@echo off
cd /d C:\ScanSnap_Roh-Scan-ecoDMS\_webservice\ecodms_webui
py -3.14-32 -m uvicorn ecodms_webui:app --host 127.0.0.1 --port 8000
pause