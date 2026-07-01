import win32serviceutil
import win32service
import win32event
import servicemanager
import subprocess
import os
import time


class EcoDMSScanService(win32serviceutil.ServiceFramework):
    _svc_name_ = "EcoDMSScanDienst"
    _svc_display_name_ = "EcoDMSScanDienst"
    _svc_description_ = "ecoDMS Scan-Service mit OCR, Metadaten und Brother-Etikettendruck"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)

        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.process = None

        self.python_exe = r"C:\Users\H.-G. Hepp\AppData\Local\Programs\Python\Python314\python.exe"

        self.script_path = (
            r"C:\ScanSnap_Roh-Scan-ecoDMS\_service\ecodms_scan_service.py"
        )

        self.working_dir = (
            r"C:\ScanSnap_Roh-Scan-ecoDMS\_service"
        )

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass

        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        servicemanager.LogInfoMsg("EcoDMSScanDienst gestartet")

        while True:
            try:
                self.process = subprocess.Popen(
                    [self.python_exe, self.script_path],
                    cwd=self.working_dir,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )

                while self.process.poll() is None:
                    rc = win32event.WaitForSingleObject(
                        self.stop_event,
                        1000
                    )

                    if rc == win32event.WAIT_OBJECT_0:
                        return

                servicemanager.LogErrorMsg(
                    f"ecodms_scan_service.py beendet mit Returncode {self.process.returncode}"
                )

                time.sleep(10)

            except Exception as e:
                servicemanager.LogErrorMsg(
                    f"Fehler im Dienst: {e}"
                )

                time.sleep(10)


if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(EcoDMSScanService)