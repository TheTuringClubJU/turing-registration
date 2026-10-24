import { useEffect, useRef, useState } from "react";
import { Html5Qrcode } from "html5-qrcode";

function QRScanner({ token, onScanComplete, disabled }) {
  const [scanning, setScanning] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const scannerRef = useRef(null);
  const isProcessingRef = useRef(false);

  const startScanner = async () => {
    setCameraError("");

    // 1. Check Secure Context requirement (HTTPS or localhost)
    if (
      window.location.protocol !== "https:" &&
      window.location.hostname !== "localhost" &&
      window.location.hostname !== "127.0.0.1"
    ) {
      setCameraError(
        "Camera access requires a secure connection (HTTPS or localhost). Browsers block camera access over raw HTTP."
      );
      return;
    }

    // 2. Check if browser supports mediaDevices
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setCameraError(
        "Your browser does not support camera access or it is disabled in settings."
      );
      return;
    }

    setScanning(true);
    await new Promise((r) => setTimeout(r, 200));

    try {
      if (!scannerRef.current) {
        scannerRef.current = new Html5Qrcode("reader");
      }
      const html5QrCode = scannerRef.current;

      const readerElem = document.getElementById("reader");
      const clientWidth = readerElem ? readerElem.clientWidth : 280;
      const boxSize = Math.floor(Math.min(clientWidth * 0.75, 240));

      const config = {
        fps: 10,
        qrbox: { width: boxSize, height: boxSize },
      };

      // Try environment (rear) camera first; if it fails, fallback to user camera, then any device
      try {
        await html5QrCode.start(
          { facingMode: "environment" },
          config,
          handleScanSuccess,
          () => {}
        );
      } catch (backCamErr) {
        console.warn("Back camera direct start failed, attempting camera list fallback:", backCamErr);
        const devices = await Html5Qrcode.getCameras();
        if (!devices || devices.length === 0) {
          throw new Error("No camera hardware detected on this device.");
        }
        // Use first available camera device ID
        await html5QrCode.start(
          devices[0].id,
          config,
          handleScanSuccess,
          () => {}
        );
      }
    } catch (err) {
      console.error("Camera startup error:", err);
      let msg = err.message || "Could not start camera.";
      if (err.name === "NotAllowedError" || msg.includes("Permission")) {
        msg = "Camera permission was denied. Please allow camera access in your browser or site settings.";
      } else if (err.name === "NotFoundError" || msg.includes("Requested device not found")) {
        msg = "No compatible camera found on this device.";
      } else if (err.name === "NotReadableError" || msg.includes("Could not start video source")) {
        msg = "Camera is currently in use by another application or tab.";
      }
      setCameraError(msg);
      setScanning(false);
    }
  };

  const handleScanSuccess = async (decodedText) => {
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
          message: data.detail || `Scan check-in failed for code: ${decodedText}`,
        });
      } else if (data.status === "checked_in" && data.method !== "qr") {
        onScanComplete({
          type: "already_checked_in",
          message: `Ticket already checked in via ${data.method ? data.method.toUpperCase() : "scanner"}.`,
          data,
        });
      } else {
        onScanComplete({
          type: "success",
          message: "Attendee admitted successfully.",
          data,
        });
      }
    } catch (err) {
      onScanComplete({
        type: "error",
        message: err.message || "Network error processing scan",
      });
    } finally {
      setTimeout(() => {
        isProcessingRef.current = false;
      }, 2000);
    }
  };

  const stopScanner = async () => {
    if (scannerRef.current && scannerRef.current.isScanning) {
      try {
        await scannerRef.current.stop();
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
            Stop Camera
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
    width: "100%",
    maxWidth: "340px",
    display: "flex",
    justifyContent: "center",
    margin: "4px 0",
  },
  scanBtn: {
    width: "100%",
    padding: "14px",
    backgroundColor: "#ffffff",
    color: "#000000",
    border: "none",
    borderRadius: "12px",
    fontWeight: "600",
    fontSize: "15px",
    cursor: "pointer",
  },
  stopBtn: {
    width: "100%",
    padding: "14px",
    backgroundColor: "#2c2c2e",
    color: "#ffffff",
    border: "none",
    borderRadius: "12px",
    fontWeight: "600",
    fontSize: "15px",
    cursor: "pointer",
  },
  errorText: {
    color: "#fca5a5",
    fontSize: "13px",
    margin: "12px 0 6px",
    textAlign: "center",
    backgroundColor: "#1c1c1e",
    padding: "12px 14px",
    borderRadius: "10px",
    border: "1px solid #3a3a3c",
    width: "100%",
    maxWidth: "340px",
    boxSizing: "border-box",
    lineHeight: "1.4",
  },
  readerBox: {
    width: "100%",
    maxWidth: "320px",
    borderRadius: "16px",
    overflow: "hidden",
    border: "1px solid #2c2c2e",
    backgroundColor: "#000",
    marginTop: "12px",
  },
};

export default QRScanner;
