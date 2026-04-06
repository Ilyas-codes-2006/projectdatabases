import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Weather from "../components/Weather";

const mockFetch = vi.fn();

const installGeolocationMock = () => {
  Object.defineProperty(globalThis.navigator, "geolocation", {
    value: {
      getCurrentPosition: (success: PositionCallback) => {
        success({
          coords: {
            latitude: 51.5074,
            longitude: -0.1278,
            accuracy: 1,
            altitude: null,
            altitudeAccuracy: null,
            heading: null,
            speed: null,
          },
          timestamp: Date.now(),
        } as GeolocationPosition);
      },
    },
    configurable: true,
  });
};

const makeDay = (offset: number) => {
  const date = new Date(Date.UTC(2026, 3, 6 + offset));
  return date.toISOString().slice(0, 10);
};

const buildResponse = ({
  dailyCodes,
  hourlyCodes,
}: {
  dailyCodes: number[];
  hourlyCodes: number[][];
}) => {
  const days = Array.from({ length: 7 }, (_, index) => makeDay(index));

  return {
    daily: {
      time: days,
      weather_code: dailyCodes,
      temperature_2m_min: [10, 11, 12, 10, 9, 8, 7],
      temperature_2m_max: [21, 22, 23, 21, 20, 19, 18],
    },
    hourly: {
      time: days.flatMap((day) => [
        `${day}T00:00`,
        `${day}T06:00`,
        `${day}T12:00`,
        `${day}T18:00`,
      ]),
      weather_code: hourlyCodes.flat(),
    },
  };
};

describe("Weather", () => {
  beforeEach(() => {
    installGeolocationMock();
    mockFetch.mockReset();
    vi.stubGlobal("fetch", mockFetch);
  });

  it("uses the 13:00 hourly icon when there is no rain", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () =>
        buildResponse({
          dailyCodes: [3, 0, 0, 0, 0, 0, 0],
          hourlyCodes: [
            [0, 0, 3, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
          ],
        }),
    });

    render(<Weather />);

    await waitFor(() => expect(mockFetch).toHaveBeenCalled());

    expect(await screen.findAllByText("☁️")).toHaveLength(1);
    expect(screen.queryAllByText("☀️")).toHaveLength(6);
  });

  it("shows rain when a day contains rain even if cloud is also present", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () =>
        buildResponse({
          dailyCodes: [0, 0, 0, 0, 0, 0, 0],
          hourlyCodes: [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [3, 3, 61, 3],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
          ],
        }),
    });

    render(<Weather />);

    await waitFor(() => expect(mockFetch).toHaveBeenCalled());

    expect(await screen.findAllByText("☀️")).toHaveLength(6);
    expect(screen.getAllByText("🌧️")).toHaveLength(1);
    expect(screen.queryAllByText("☁️")).toHaveLength(0);
  });
});


