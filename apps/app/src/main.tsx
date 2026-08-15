import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { App } from "./App";
import { AuthProvider } from "./lib/auth";
import { initTheme } from "./lib/theme";
import "./styles.css";

initTheme();

/**
 * The router is outside the auth provider on purpose: dev auth's screens use
 * `useNavigate`, so they have to be inside a Router to exist at all. Clerk does
 * not mind either order.
 */
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
);
