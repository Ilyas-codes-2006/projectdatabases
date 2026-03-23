import { useState } from "react";

export default function Calendar() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [availableDates, setAvailableDates] = useState<string[]>([]);

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

  const saveAvailability = () => {
    console.log("Datums om op te slaan:", availableDates);
    alert(`You have saved ${availableDates.length} available days!`);
    // TODO add fetch() for backend
  };

  return (
    <div className="max-w-md w-full mx-auto bg-white p-6 rounded-lg shadow-md border border-gray-200">
      <div className="flex justify-between items-center mb-4">
        <button
          onClick={prevMonth}
          className="p-2 text-gray-600 hover:bg-gray-100 rounded-full cursor-pointer"
        >
          &larr;
        </button>
        <h2 className="text-xl font-bold text-gray-800">
          {monthNames[month]} {year}
        </h2>
        <button
          onClick={nextMonth}
          className="p-2 text-gray-600 hover:bg-gray-100 rounded-full cursor-pointer"
        >
          &rarr;
        </button>
      </div>

      <div className="grid grid-cols-7 gap-1 mb-2 text-center text-sm font-medium text-gray-500">
        <div>Mo</div>
        <div>Tue</div>
        <div>Wed</div>
        <div>Thu</div>
        <div>Fri</div>
        <div>Sat</div>
        <div>Sun</div>
      </div>
      <div className="grid grid-cols-7 gap-1">
        {Array.from({ length: startOffset }).map((_, i) => (
          <div key={`empty-${i}`} className="p-2"></div>
        ))}

        {Array.from({ length: daysInMonth }).map((_, i) => {
          const day = i + 1;
          const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
          const isSelected = availableDates.includes(dateStr);

          return (
            <button
              key={day}
              onClick={() => handleDateClick(day)}
              className={`p-2 rounded-md text-sm font-semibold transition-colors cursor-pointer
                ${
                  isSelected
                    ? "bg-green-500 text-white hover:bg-green-600"
                    : "bg-gray-50 text-gray-700 hover:bg-gray-200 border border-gray-100"
                }`}
            >
              {day}
            </button>
          );
        })}
      </div>

      <button
        onClick={saveAvailability}
        className="w-full mt-6 bg-blue-600 text-white font-semibold py-2 rounded-md hover:bg-blue-700 transition-colors cursor-pointer"
      >
        Beschikbaarheid Opslaan
      </button>
    </div>
  );
}
