import { useEffect, useState } from "react";

interface WeatherDay {
  date: string;
  dayName: string;
  tempMin: number;
  tempMax: number;
  description: string;
  icon: string;
}

export default function Weather() {
  const [weatherData, setWeatherData] = useState<WeatherDay[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [location, setLocation] = useState<{ lat: number; lon: number } | null>(null);

  useEffect(() => {
    // Get user's geolocation
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            lat: position.coords.latitude,
            lon: position.coords.longitude,
          });
        },
        () => {
          // Fallback to a default location (e.g., London)
          setLocation({ lat: 51.5074, lon: -0.1278 });
        }
      );
    } else {
      setLocation({ lat: 51.5074, lon: -0.1278 });
    }
  }, []);

  useEffect(() => {
    if (!location) return;

    const fetchWeather = async () => {
      try {
        setLoading(true);
        setError(null);

        // Using Open-Meteo API (free, no authentication required)
        const response = await fetch(
          `https://api.open-meteo.com/v1/forecast?latitude=${location.lat}&longitude=${location.lon}&daily=weather_code,temperature_2m_max,temperature_2m_min&hourly=weather_code&timezone=auto&forecast_days=7`
        );

        if (!response.ok) {
          throw new Error("Failed to fetch weather data");
        }

        const data = await response.json();

        const dailyData = data.daily;
        const weatherDays: WeatherDay[] = [];

        for (let i = 0; i < 7; i++) {
          const date = new Date(dailyData.time[i]);
          const dayName = date.toLocaleDateString("en-US", { weekday: "short" });

          // Prefer precipitation when present; otherwise fall back to the 13:00 hourly code.
          const weatherCode =
            getRepresentativeWeatherCode(
              dailyData.time[i],
              dailyData.weather_code[i],
              data.hourly
            );
          const { description, icon } = getWeatherInfo(weatherCode);

          weatherDays.push({
            date: date.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
            dayName,
            tempMin: Math.round(dailyData.temperature_2m_min[i]),
            tempMax: Math.round(dailyData.temperature_2m_max[i]),
            description,
            icon,
          });
        }

        setWeatherData(weatherDays);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load weather");
      } finally {
        setLoading(false);
      }
    };

    fetchWeather();
  }, [location]);

  const getWeatherInfo = (code: number): { description: string; icon: string } => {
    // WMO Weather interpretation codes (https://open-meteo.com/en/docs)
    // 0: Clear sky
    if (code === 0) return { description: "Clear", icon: "☀️" };
    // 1, 2: Mainly clear, partly cloudy, and overcast
    if (code === 1) return { description: "Mostly clear", icon: "🌤️" };
    if (code === 2) return { description: "Partly cloudy", icon: "⛅" };
    if (code === 3) return { description: "Overcast", icon: "☁️" };
    // 45, 48: Foggy, and depositing rime fog
    if (code === 45 || code === 48) return { description: "Foggy", icon: "🌫️" };
    // 51, 53, 55: Drizzle: Light, moderate, and dense intensity
    if (code === 51 || code === 53 || code === 55) return { description: "Drizzle", icon: "🌦️" };
    // 61, 63, 65: Rain: Slight, moderate and heavy intensity
    if (code === 61 || code === 63 || code === 65) return { description: "Rain", icon: "🌧️" };
    // 71, 73, 75: Snow: Slight, moderate, and heavy intensity
    if (code === 71 || code === 73 || code === 75) return { description: "Snow", icon: "❄️" };
    // 77: Snow grains
    if (code === 77) return { description: "Snow grains", icon: "❄️" };
    // 80, 81, 82: Rain showers: Slight, moderate, and violent
    if (code === 80 || code === 81 || code === 82) return { description: "Rain showers", icon: "🌧️" };
    // 85, 86: Snow showers slight and heavy
    if (code === 85 || code === 86) return { description: "Snow showers", icon: "❄️" };
    // 95, 96, 99: Thunderstorm: Slight or moderate, with slight and heavy hail
    if (code === 95 || code === 96 || code === 99) return { description: "Thunderstorm", icon: "⛈️" };
    return { description: "Unknown", icon: "🌡️" };
  };

  const getRepresentativeWeatherCode = (
    day: string,
    dailyCode: number,
    hourly?: { time?: string[]; weather_code?: number[] }
  ): number => {
    if (!hourly?.time?.length || !hourly.weather_code?.length) return dailyCode;

    let bestWetCode: number | null = null;
    let bestWetPriority = -1;

    hourly.time.forEach((time, index) => {
      if (!time.startsWith(day) || hourly.weather_code?.[index] === undefined) return;

      const code = hourly.weather_code[index] ?? null;
      if (code === null) return;

      const priority = getPrecipitationPriority(code);

      if (priority > 0) {
        if (priority > bestWetPriority) {
          bestWetPriority = priority;
          bestWetCode = code;
        }
      }
    });

    if (bestWetCode !== null) {
      return bestWetCode;
    }

    const fallbackTime = `${day}T13:00`;
    const fallbackIndex = hourly.time.findIndex((time) => time === fallbackTime);
    if (fallbackIndex >= 0) {
      const fallbackCode = hourly.weather_code[fallbackIndex];
      if (fallbackCode !== undefined) {
        return fallbackCode;
      }
    }

    return dailyCode;
  };

  const getPrecipitationPriority = (code: number): number => {
    if (code === 95 || code === 96 || code === 99) return 4;
    if (code === 71 || code === 73 || code === 75 || code === 77 || code === 85 || code === 86) {
      return 3;
    }
    if (code === 51 || code === 53 || code === 55 || code === 61 || code === 63 || code === 65 || code === 80 || code === 81 || code === 82) {
      return 2;
    }
    if (code === 45 || code === 48) return 1;
    return 0;
  };

  if (loading) {
    return (
      <div className="weather-container">
        <div className="weather-loading">Loading weather...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="weather-container">
        <div className="weather-error">{error}</div>
      </div>
    );
  }

  return (
    <div className="weather-container">
      <div className="weather-header">
        <h3>7 day weather forecast</h3>
      </div>
      <div className="weather-grid">
        {weatherData.map((day, index) => (
          <div key={index} className="weather-card">
            <div className="weather-day">{day.dayName}</div>
            <div className="weather-date">{day.date}</div>
            <div className="weather-icon">{day.icon}</div>
            <div className="weather-temps">
              <span className="weather-max">{day.tempMax}°</span>
              <span className="weather-min">{day.tempMin}°</span>
            </div>
            <div className="weather-description">{day.description}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

