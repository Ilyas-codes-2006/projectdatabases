import { useMessage } from "../hooks/useMessage";
import MessageBanner from "../components/MessageBanner";
import Calendar from "../components/Calendar";

export default function Availability() {
  const { message, clearMessage, showMessage } = useMessage();

  return (
    <div style={{ padding: "4rem 2rem", maxWidth: "800px", margin: "0 auto" }}>
      <MessageBanner message={message} onClose={clearMessage} />

      <h1 style={{ marginBottom: "1rem" }}>Set Your Availability</h1>
      <p style={{ marginBottom: "2rem", color: "var(--text-muted)" }}>
        Select when you would be available to play matches and save these dates.
      </p>

      <div className="calendar-wrapper">
        <Calendar showMessage={showMessage} readOnly={false} />
      </div>
    </div>
  );
}
