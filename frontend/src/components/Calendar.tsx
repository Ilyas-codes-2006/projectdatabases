import { useState, useEffect } from "react";
import { useMessage } from "../hooks/useMessage";

interface CalendarProps {
  showMessage: (text: string, type: "error" | "success") => void;
}

export default function Calendar({ showMessage }: CalendarProps) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  useEffect(() => {
    const fetchAvailability = async () => {
      try {
        const token = localStorage.getItem("token");
        if (!token) return;

        const response = await fetch("http://localhost:5000/api/availability", {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          setAvailableDates(data.dates);
        }
      } catch (error) {
        console.error("Error while retrieving availability:", error);
      }
    };

    fetchAvailability();
  }, []);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDayOfMonth = new Date(year, month, 1).getDay();

  const startOffset = firstDayOfMonth === 0 ? 6 : firstDayOfMonth - 1;

  const monthNames = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];

  const handleDateClick = (day: number) => {
    const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;

    setAvailableDates((prev) =>
      prev.includes(dateStr)
        ? prev.filter((d) => d !== dateStr)
        : [...prev, dateStr],
    );
  };

  const nextMonth = () => setCurrentDate(new Date(year, month + 1, 1));
  const prevMonth = () => setCurrentDate(new Date(year, month - 1, 1));

  const saveAvailability = async () => {
    try {
      const token = localStorage.getItem("token");

      const response = await fetch("/api/availability", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ dates: availableDates }),
      });

      const data = await response.json();

      if (response.ok) {
        showMessage("🎉 " + data.message, "success");
      } else {
        showMessage("Error: " + data.error, "error");
      }
    } catch (error) {
      console.error("Error while saving:", error);
      showMessage(
        "Something went wrong while trying to connect to the server.",
        "error",
      );
    }
  };

  return (
    <div className="calendar-container">
      <div className="calendar-header">
        <button onClick={prevMonth} className="calendar-nav-btn">
          &larr;
        </button>
        <h2>
          {monthNames[month]}{" "}
          <span style={{ color: "var(--text-muted)" }}>{year}</span>
        </h2>
        <button onClick={nextMonth} className="calendar-nav-btn">
          &rarr;
        </button>
      </div>

      <div className="calendar-grid">
        {["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"].map((day) => (
          <div key={day} className="calendar-day-header">
            {day}
          </div>
        ))}

        {Array.from({ length: startOffset }).map((_, i) => (
          <div key={`empty-${i}`} />
        ))}

        {Array.from({ length: daysInMonth }).map((_, i) => {
          const day = i + 1;
          const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
          const isSelected = availableDates.includes(dateStr);

          return (
            <button
              key={day}
              onClick={() => handleDateClick(day)}
              className={`calendar-day ${isSelected ? "selected" : ""}`}
            >
              {day}
            </button>
          );
        })}
      </div>

      <button
        onClick={saveAvailability}
        className="btn-submit"
        style={{ marginTop: "1.5rem" }}
      >
        Save Availability
      </button>
    </div>
  );
}
