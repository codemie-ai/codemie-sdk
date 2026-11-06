import { jest, describe, expect, it, beforeEach } from "@jest/globals";
import { ZodError } from "zod";
import { ProjectService } from "../../../src/services/project";
import { ApiRequestHandler } from "../../../src/utils/http";
import { ApiError, NotFoundError } from "../../../src/exceptions";

jest.mock("../../../src/utils/http", () => ({
  ApiRequestHandler: jest.fn(),
}));

describe("ProjectService", () => {
  const config = { apiDomain: "https://api.example.com", token: "t" };
  let service: ProjectService;
  let api: any;

  const users = (n: number) =>
    Array.from({ length: n }, (_, i) => ({ user_id: `u${i}`, is_project_admin: false }));
  const ids = (n: number) =>
    Array.from({ length: n }, (_, i) => `${String(i).padStart(8, "0")}-aaaa-bbbb-cccc-dddddddddddd`);

  beforeEach(() => {
    api = {
      get: jest.fn(),
      post: jest.fn(),
      put: jest.fn(),
      patch: jest.fn(),
      delete: jest.fn(),
      postMultipart: jest.fn(),
    };
    (ApiRequestHandler as unknown as jest.Mock).mockImplementation(() => api);
    service = new ProjectService(config);
  });

  it("createProject posts the request and unwraps data", async () => {
    api.post.mockResolvedValue({ data: { name: "p" } });
    const req = { name: "p", cli_analytics_enabled: true };

    const result = await service.createProject(req);

    expect(api.post).toHaveBeenCalledWith("/v1/projects", req);
    expect(result).toEqual({ name: "p" });
  });

  it("falls back to the body when data is absent", async () => {
    api.get.mockResolvedValue({ name: "p", members: [] });

    const result = await service.getProjectDetail("p");

    expect(result).toEqual({ name: "p", members: [] });
  });

  it("getProjectDetail gets the encoded url and unwraps data", async () => {
    api.get.mockResolvedValue({ data: { name: "a b", members: [] } });

    const result = await service.getProjectDetail("a b");

    expect(api.get).toHaveBeenCalledWith("/v1/projects/a%20b");
    expect(result).toEqual({ name: "a b", members: [] });
  });

  describe("empty ids", () => {
    it("rejects an empty projectName without a request", async () => {
      await expect(service.getProjectDetail("")).rejects.toThrow("must not be empty");
      expect(api.get).not.toHaveBeenCalled();
    });
  });

  describe("listProjects", () => {
    it("types current_spending on list items", async () => {
      const item: import("../../../src/models/project").ProjectListItem = {
        name: "p",
        project_type: "shared",
        user_count: 1,
        admin_count: 1,
        current_spending: 1.5,
      };
      api.get.mockResolvedValue({ data: [item], pagination: {} });
      const result: any = await service.listProjects();
      expect(result.data[0].current_spending).toBe(1.5);
    });

    it("sends the default query and returns the raw body", async () => {
      const body = { data: [], pagination: { total: 0, page: 0, per_page: 20 } };
      api.get.mockResolvedValue(body);

      const result = await service.listProjects();

      expect(api.get).toHaveBeenCalledWith("/v1/projects", {
        page: 0,
        per_page: 20,
        include_counters: "True",
        include_budgets: "False",
        has_assigned_budgets: "False",
        sort_order: "asc",
      });
      expect(result).toBe(body);
    });

    it("adds search and sort_by only when set", async () => {
      api.get.mockResolvedValue({ data: [], pagination: {} });

      await service.listProjects({
        search: "x",
        sort_by: "name",
        sort_order: "desc",
        page: 2,
        per_page: 50,
        include_counters: false,
        include_budgets: true,
        has_assigned_budgets: true,
      });

      expect(api.get).toHaveBeenCalledWith("/v1/projects", {
        page: 2,
        per_page: 50,
        include_counters: "False",
        include_budgets: "True",
        has_assigned_budgets: "True",
        sort_order: "desc",
        search: "x",
        sort_by: "name",
      });
    });
  });

  describe("updateProject", () => {
    it("always sends both clear flags", async () => {
      api.patch.mockResolvedValue({ data: { name: "n" } });

      const result = await service.updateProject("p", { display_name: "D", description: undefined });

      expect(api.patch).toHaveBeenCalledWith("/v1/projects/p", {
        display_name: "D",
        clear_description: false,
        clear_cost_center: false,
      });
      expect(result).toEqual({ name: "n" });
    });

    it("passes explicit clear flags and other fields", async () => {
      api.patch.mockResolvedValue({});

      await service.updateProject("p", {
        clear_description: true,
        cli_analytics_enabled: false,
        enforce_member_spend_limits: true,
      });

      expect(api.patch).toHaveBeenCalledWith("/v1/projects/p", {
        clear_description: true,
        clear_cost_center: false,
        cli_analytics_enabled: false,
        enforce_member_spend_limits: true,
      });
    });
  });

  it("deleteProject encodes the name and unwraps data", async () => {
    api.delete.mockResolvedValue({ data: { message: "ok", name: "x/assignments" } });

    const result = await service.deleteProject("x/assignments");

    expect(api.delete).toHaveBeenCalledWith("/v1/projects/x%2Fassignments");
    expect(result).toEqual({ message: "ok", name: "x/assignments" });
  });

  it("transferOwnership puts the user id and returns the raw body", async () => {
    const body = { data: "kept", name: "p", created_by: "u", message: "m" };
    api.put.mockResolvedValue(body);

    const result = await service.transferOwnership("p q", "u/1");

    expect(api.put).toHaveBeenCalledWith("/v1/projects/p%20q/ownership", { user_id: "u/1" });
    expect(result).toBe(body);
  });

  it("assignUserToProject defaults is_project_admin to false", async () => {
    api.post.mockResolvedValue({ data: { message: "m" } });

    const result = await service.assignUserToProject("p", "u1");

    expect(api.post).toHaveBeenCalledWith("/v1/projects/p/assignment", {
      user_id: "u1",
      is_project_admin: false,
    });
    expect(result).toEqual({ message: "m" });
  });

  it("assignUserToProject sends the admin flag", async () => {
    api.post.mockResolvedValue({});
    await service.assignUserToProject("p", "u1", true);
    expect(api.post).toHaveBeenCalledWith("/v1/projects/p/assignment", {
      user_id: "u1",
      is_project_admin: true,
    });
  });

  it("updateUserProjectAssignment puts to the encoded user url", async () => {
    api.put.mockResolvedValue({ data: { message: "m" } });

    const result = await service.updateUserProjectAssignment("p", "a/b", true);

    expect(api.put).toHaveBeenCalledWith("/v1/projects/p/assignment/a%2Fb", {
      is_project_admin: true,
    });
    expect(result).toEqual({ message: "m" });
  });

  it("removeUserFromProject deletes the encoded user url", async () => {
    api.delete.mockResolvedValue({ data: { message: "m" } });

    const result = await service.removeUserFromProject("p", "a/b");

    expect(api.delete).toHaveBeenCalledWith("/v1/projects/p/assignment/a%2Fb");
    expect(result).toEqual({ message: "m" });
  });

  describe("bulkAssignUsersToProject", () => {
    it("posts users and unwraps data", async () => {
      api.post.mockResolvedValue({ data: { total: 1 } });
      const u = users(1);

      const result = await service.bulkAssignUsersToProject("p", u);

      expect(api.post).toHaveBeenCalledWith("/v1/projects/p/assignments", { users: u });
      expect(result).toEqual({ total: 1 });
    });

    it("accepts 1000 users", async () => {
      api.post.mockResolvedValue({});
      await service.bulkAssignUsersToProject("p", users(1000));
      expect(api.post).toHaveBeenCalledTimes(1);
    });

    it.each([0, 1001])("rejects %i users without a request", async (n) => {
      await expect(service.bulkAssignUsersToProject("p", users(n))).rejects.toBeInstanceOf(
        ZodError,
      );
      expect(api.post).not.toHaveBeenCalled();
    });
  });

  describe("bulkRemoveUsersFromProject", () => {
    it("deletes with a repeated-key serializer", async () => {
      api.delete.mockResolvedValue({ data: { total: 100 } });

      const result = await service.bulkRemoveUsersFromProject("p", ids(100));

      const [path, cfg] = api.delete.mock.calls[0];
      expect(path).toBe("/v1/projects/p/assignments");
      expect(cfg.params).toEqual({ user_id: ids(100) });
      const query: string = cfg.paramsSerializer(cfg.params);
      expect(query).toBe(ids(100).map((i) => `user_id=${i}`).join("&"));
      expect(query).not.toContain("[]");
      expect(result).toEqual({ total: 100 });
    });

    it.each([0, 101])("rejects %i ids without a request", async (n) => {
      await expect(service.bulkRemoveUsersFromProject("p", ids(n))).rejects.toBeInstanceOf(
        ZodError,
      );
      expect(api.delete).not.toHaveBeenCalled();
    });
  });

  describe("csv", () => {
    it.each<["validateUsersFromCsv" | "importUsersFromCsv", string]>([
      ["validateUsersFromCsv", "/v1/projects/p/import-users/validate"],
      ["importUsersFromCsv", "/v1/projects/p/import-users"],
    ])("%s uploads multipart", async (method, url) => {
      api.postMultipart.mockResolvedValue({ data: { users: [] } });

      const result = await service[method]("p", Buffer.from("email,role"));

      const [calledUrl, form] = api.postMultipart.mock.calls[0];
      expect(calledUrl).toBe(url);
      expect(form.getBuffer().toString()).toContain('filename="users.csv"');
      expect(form.getBuffer().toString()).toContain('name="file"');
      expect(form.getBuffer().toString()).toContain("Content-Type: text/csv");
      expect(result).toEqual({ users: [] });
    });

    it("uses a custom filename", async () => {
      api.postMultipart.mockResolvedValue({});
      await service.importUsersFromCsv("p", Buffer.from("x"), "a.csv");
      expect(api.postMultipart.mock.calls[0][1].getBuffer().toString()).toContain(
        'filename="a.csv"',
      );
    });
  });

  describe("projectExists", () => {
    it("returns true on success", async () => {
      api.get.mockResolvedValue({ data: { name: "p" } });
      await expect(service.projectExists("p")).resolves.toBe(true);
    });

    it("returns false on NotFoundError", async () => {
      api.get.mockRejectedValue(new NotFoundError("Resource", "unknown"));
      await expect(service.projectExists("p")).resolves.toBe(false);
    });

    it.each([
      new ApiError("unauthorized", 401),
      new ApiError("boom", 500),
      new Error("network"),
    ])("rethrows %s", async (err) => {
      api.get.mockRejectedValue(err);
      await expect(service.projectExists("p")).rejects.toBe(err);
    });
  });
});
