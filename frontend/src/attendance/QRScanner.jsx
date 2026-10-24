import { useEffect, useRef, useState } from "react";
import { Html5Qrcode } from "html5-qrcode";

function QRScanner({ token, onScanComplete, disabled }) {
  const [scanning, setScanning] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const scannerRef = useRef(null);
  const isProcessingRef = useRef(false);

  const startScanner = async () => {
    setCameraError("");
    try {
      const html5QrCode = new Html5Qrcode("reader");
      scannerRef.current = html5QrCode;

      const config = {
        fps: 10,
        qrbox: { width: 240, height: 240 },
      };

      await html5QrCode.start(
        { facingMode: "environment" },
        config,
        async (decodedText) => {
          if (isProcessingRef.current) return;
          isProcessingRef.current = true;

          try {
            const response = await fetch("/attendance/scan", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
              },
              body: JSON.stringify({ registration_id: decodedText.trim() }),
            });

            const data = await response.json();

            if (!response.ok) {
              onScanComplete({
                type: "error",
                message: data.detail || "Scan verification failed",
              });
            } else if (data.status === "checked_in" && data.method !== "qr") {
              onScanComplete({
                type: "already_checked_in",
                message: `This attendee was previously checked in via ${data.method ? data.method.toUpperCase() : "scanner"}.`,
                data,
              });
            } else {
              onScanComplete({
                type: "success",
                message: "Attendee checked in successfully.",
                data,
              });
            }
          } catch (err) {
            onScanComplete({
              type: "error",
              message: err.message || "Network error while processing scan",
            });
          } finally {
            setTimeout(() => {
              isProcessingRef.current = false;
            }, 2000);
          }
        },
        () => {}
      );

      setScanning(true);
    } catch (err) {
      setCameraError(
        err.message || "Unable to access camera. Please allow camera permissions."
      );
      setScanning(false);
    }
  };

  const stopScanner = async () => {
    if (scannerRef.current && scannerRef.current.isScanning) {
      try {
        await scannerRef.current.stop();
        await scannerRef.current.clear();
      } catch (err) {
        console.error("Error stopping scanner:", err);
      }
    }
    setScanning(false);
  };

  useEffect(() => {
    return () => {
      if (scannerRef.current && scannerRef.current.isScanning) {
        scannerRef.current.stop().catch(() => {});
      }
    };
  }, []);

  return (
    <div style={styles.container}>
      <div style={styles.controls}>
        {!scanning ? (
          <button
            onClick={startScanner}
            disabled={disabled}
            style={disabled ? { ...styles.scanBtn, opacity: 0.4 } : styles.scanBtn}
          >
            Start Camera Scanner
          </button>
        ) : (
          <button onClick={stopScanner} style={styles.stopBtn}>
            Stop Scanner
          </button>
        )}
      </div>

      {cameraError && <div style={styles.errorText}>{cameraError}</div>}

      <div
        id="reader"
        style={{
          ...styles.readerBox,
          display: scanning ? "block" : "none",
        }}
      />
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    width: "100%",
  },
  controls: {
    margin: "8px 0",
  },
  scanBtn: {
    padding: "10px 22px",
    backgroundColor: "#ffffff",
    color: "#000000",
    border: "none",
    borderRadius: "10px",
    fontWeight: "600",
    fontSize: "13px",
    cursor: "pointer",
    letterSpacing: "-0.01em",
  },
  stopBtn: {
    padding: "10px 22px",
    backgroundColor: "#2c2c2e",
    color: "#ffffff",
    border: "none",
    borderRadius: "10px",
    fontWeight: "600",
    fontSize: "13px",
    cursor: "pointer",
  },
  errorText: {
    color: "#86868b",
    fontSize: "13px",
    marginTop: "8px",
    textAlign: "center",
  },
  readerBox: {
    width: "100%",
    maxWidth: "340px",
    borderRadius: "12px",
    overflow: "hidden",
    border: "1px solid #2c2c2e",
    marginTop: "12px",
  },
};

export default QRScanner;
