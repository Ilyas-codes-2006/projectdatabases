import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { useEffect } from "react";
import { AuthProvider } from "./context/AuthContext";
import { MessageProvider, useMessageContext } from "./context/MessageContext.tsx";
import Navbar from "./components/Navbar";

import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import Admin from "./pages/Admin";
import NotFound from "./pages/notfound";
import ServerError from "./pages/servererror";
import BadGateway from "./pages/badgateway";

import "./App.css";

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => window.scrollTo(0, 0), [pathname]);
  return null;
}

function GlobalMessageBanner() {
  const { message, clearMessage } = useMessageContext();
  if (!message) return null;
  return (
    <div className={`message-banner ${message.type}`} onClick={clearMessage}>
      {message.text} <span className="message-close">×</span>
    </div>
  );
}

function Layout() {
  return (
    <>
      <ScrollToTop />
      <Navbar />
      <GlobalMessageBanner />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/500" element={<ServerError />} />
        <Route path="/502" element={<BadGateway />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  );
}

export default function App() {
  return (
    <MessageProvider>
      <AuthProvider>
        <BrowserRouter>
          <div className="app">
            <Layout />
          </div>
        </BrowserRouter>
      </AuthProvider>
    </MessageProvider>
  );
}