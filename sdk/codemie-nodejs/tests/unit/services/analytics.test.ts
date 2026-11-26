import { jest, describe, expect, it, beforeEach } from "@jest/globals";
import { AnalyticsService } from "../../../src/services/analytics";
import { ApiRequestHandler } from "../../../src/utils/http";

jest.mock("../../../src/utils/http", () => ({
  ApiRequestHandler: jest.fn(),
}));

describe("AnalyticsService headroom", () => {
  let service: AnalyticsService;
  let apiHandler: jest.Mocked<ApiRequestHandler>;

  beforeEach(() => {
    apiHandler = {
      client: {},
      get: jest.fn(),
      post: jest.fn(),
      put: jest.fn(),
      delete: jest.fn(),
      stream: jest.fn(),
      request: jest.fn(),
      throwIfResponseError: jest.fn(),
    } as unknown as jest.Mocked<ApiRequestHandler>;
    (ApiRequestHandler as jest.Mock).mockImplementation(() => apiHandler);
    service = new AnalyticsService({ apiDomain: "https://api.example.com", token: "t" });
  });

  const filters = {
    users: "u1,u2",
    projects: "p1",
    start_date: "2026-01-01T00:00:00Z",
    end_date: "2026-01-02T00:00:00Z",
  };

  describe("getHeadroomSummary", () => {
    it("hits the summary endpoint and forwards filters", async () => {
      apiHandler.get.mockResolvedValue({ data: { metrics: [] } });

      const result = await service.getHeadroomSummary({ time_period: "last_7_days" });

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/analytics/headroom/summary", {
        time_period: "last_7_days",
      });
      expect(result).toEqual({ data: { metrics: [] } });
    });

    it("sends no pagination or assistant keys", async () => {
      apiHandler.get.mockResolvedValue({});

      await service.getHeadroomSummary({ ...filters, page: 3, assistant_id: "a" } as never);

      const params = apiHandler.get.mock.calls[0][1] as Record<string, unknown>;
      expect(params).toEqual(filters);
      expect("page" in params).toBe(false);
      expect("per_page" in params).toBe(false);
      expect("assistant_id" in params).toBe(false);
      expect("client_source" in params).toBe(false);
    });

    it("sends an empty query without params", async () => {
      apiHandler.get.mockResolvedValue({});

      await service.getHeadroomSummary();

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/analytics/headroom/summary", {});
    });

    it("rejects an invalid start_date", async () => {
      await expect(service.getHeadroomSummary({ start_date: "not-a-date" })).rejects.toThrow();
      expect(apiHandler.get).not.toHaveBeenCalled();
    });
  });

  describe("getHeadroomTimeseries", () => {
    it("hits the timeseries endpoint and forwards filters", async () => {
      apiHandler.get.mockResolvedValue({ data: { columns: [], rows: [] } });

      await service.getHeadroomTimeseries(filters);

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/analytics/headroom/timeseries", filters);
    });

    it("sends no pagination keys", async () => {
      apiHandler.get.mockResolvedValue({});

      await service.getHeadroomTimeseries({ ...filters, per_page: 5 } as never);

      const params = apiHandler.get.mock.calls[0][1] as Record<string, unknown>;
      expect("page" in params).toBe(false);
      expect("per_page" in params).toBe(false);
    });

    it("rejects an invalid end_date", async () => {
      await expect(service.getHeadroomTimeseries({ end_date: "nope" })).rejects.toThrow();
    });
  });

  describe("getHeadroomByStrategy", () => {
    it("hits the by-strategy endpoint with default pagination", async () => {
      apiHandler.get.mockResolvedValue({ data: { columns: [], rows: [] } });

      await service.getHeadroomByStrategy();

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/analytics/headroom/by-strategy", {
        page: 0,
        per_page: 20,
      });
    });

    it("forwards pagination and filters", async () => {
      apiHandler.get.mockResolvedValue({});

      await service.getHeadroomByStrategy({ ...filters, page: 2, per_page: 5 });

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/analytics/headroom/by-strategy", {
        ...filters,
        page: 2,
        per_page: 5,
      });
    });

    it("rejects an invalid start_date", async () => {
      await expect(service.getHeadroomByStrategy({ start_date: "x" })).rejects.toThrow();
    });
  });
});
