import { useState } from "react";

function OrganiserLogin() {
    const [userId, setUserId] = useState("");
    const [password, setPassword] = useState("");

    const handleLogin = (event) => {
        event.preventDefault();

        // Backend authentication will be added later
        console.log("User ID:", userId);
        console.log("Password:", password);
    };

    return (
        <div style={styles.page}>

            <form style={styles.form} onSubmit={handleLogin}>

                <h1 style={styles.heading}>Login</h1>

                <label style={styles.label} htmlFor="userId">
                    User ID
                </label>

                <input
                    style={styles.input}
                    type="text"
                    id="userId"
                    name="userId"
                    placeholder="Enter User ID"
                    value={userId}
                    onChange={(event) => setUserId(event.target.value)}
                    required
                />

                <label style={styles.label} htmlFor="password">
                    Password
                </label>

                <input
                    style={styles.input}
                    type="password"
                    id="password"
                    name="password"
                    placeholder="Enter Password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    required
                />

                <button style={styles.button} type="submit">
                    Login
                </button>

            </form>

        </div>
    );
}

const styles = {
    page: {
        minHeight: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        backgroundColor: "#f4f4f4",
        fontFamily: "Arial, sans-serif"
    },

    form: {
        width: "100%",
        maxWidth: "350px",
        padding: "30px",
        backgroundColor: "white",
        border: "1px solid #ddd",
        borderRadius: "8px"
    },

    heading: {
        textAlign: "center",
        marginBottom: "25px",
        fontSize: "24px"
    },

    label: {
        display: "block",
        marginBottom: "6px",
        fontWeight: "600"
    },

    input: {
        width: "100%",
        padding: "11px",
        marginBottom: "18px",
        border: "1px solid #ccc",
        borderRadius: "5px",
        fontSize: "15px",
        boxSizing: "border-box"
    },

    button: {
        width: "100%",
        padding: "11px",
        border: "none",
        borderRadius: "5px",
        backgroundColor: "#333",
        color: "white",
        fontSize: "15px",
        fontWeight: "600",
        cursor: "pointer"
    }
};

export default OrganiserLogin;