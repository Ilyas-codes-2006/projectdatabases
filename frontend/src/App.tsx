import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { useEffect } from "react";
import { AuthProvider } from "./context/AuthContext";
import Navbar from "./components/Navbar";

import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import Teams from "./pages/Teams";
import JoinTeams from "./pages/JoinTeams";
import Clubs from "./pages/Clubs";
import Admin from "./pages/Admin";
import AdminClubRequests from "./pages/AdminClubRequests";
import MyClub from "./pages/MyClub";
import Profile from "./pages/Profile";
import NotFound from "./pages/notfound";
import ServerError from "./pages/servererror";
import BadGateway from "./pages/badgateway";
import ChangeEmail from "./pages/ChangeMail";
import ChangeName from "./pages/ChangeName";
import ChangeBirthday from "./pages/ChangeBirthday";
import Availability from "./pages/Availability";

import "./App.css";

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => window.scrollTo(0, 0), [pathname]);
  return null;
}

function Layout() {
  return (
    <>
      <ScrollToTop />
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/teams" element={<Teams />} />
        <Route path="/teams/join" element={<JoinTeams />} />
        <Route path="/clubs" element={<Clubs />} />
        <Route path="/availability" element={<Availability />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/profile/change-email" element={<ChangeEmail />} />
        <Route path="/profile/change-name" element={<ChangeName />} />
        <Route path="/profile/change-birthday" element={<ChangeBirthday />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/admin/club-requests" element={<AdminClubRequests />} />
        <Route path="/my-club" element={<MyClub />} />
        <Route path="/500" element={<ServerError />} />
        <Route path="/502" element={<BadGateway />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="app">
          <Layout />
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}
