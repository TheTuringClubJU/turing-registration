import { useEffect, useState } from "react";
import AttendanceDashboard from "./attendance/AttendanceDashboard";
import OrganiserLogin from "./attendance/OrganiserLogin";
import RegistrationForm from "./registration/RegistrationForm";
import "./registration/registration.css";

function App() {
  const [token, setToken] = useState(() => localStorage.getItem("organiser_token") || "");

  useEffect(() => {
    const handleStorageChange = () => {
      setToken(localStorage.getItem("organiser_token") || "");
    };
    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);

  const handleLoginSuccess = (newToken) => {
    setToken(newToken);
  };

  const handleLogout = () => {
    localStorage.removeItem("organiser_token");
    setToken("");
  };

  if (window.location.pathname.replace(/\/$/, "") === "/register") {
    return <main className="registration-page"><RegistrationForm /></main>;
  }

  if (!token) {
    return <OrganiserLogin onLoginSuccess={handleLoginSuccess} />;
  }

  return <AttendanceDashboard token={token} onLogout={handleLogout} />;
}

export default App;
