import { jest, describe, expect, it, beforeEach } from "@jest/globals";
import { UserService } from "../../../src/services/user";
import { ApiRequestHandler } from "../../../src/utils/http";
import { AboutUserResponse, UserData } from "../../../src/models/user";
import { ApiError } from "../../../src/exceptions";

jest.mock("../../../src/utils/http", () => ({
  ApiRequestHandler: jest.fn(),
}));

describe("UserService", () => {
  const domain = "https://api.example.com";
  const token = "test-token";
  let service: UserService;
  let apiHandler: jest.Mocked<ApiRequestHandler>;

  const mockUser: AboutUserResponse = {
    user_id: "123",
    username: "testuser",
    name: "Test User",
    is_admin: false,
    applications: ["app1", "app2"],
    applications_admin: [],
    picture: "https://example.com/avatar.jpg",
    knowledge_bases: ["kb1"],
    email: ""
  };

  const mockUserData: UserData = {
    id: "123",
    user_id: "123",
    date: "2023-01-01T00:00:00Z",
    update_date: "2023-01-02T00:00:00Z",
  };

  beforeEach(() => {
    apiHandler = {
      client: {} as any,
      get: jest.fn(),
      post: jest.fn(),
      put: jest.fn(),
      delete: jest.fn(),
      stream: jest.fn(),
      request: jest.fn(),
      throwIfResponseError: jest.fn(),
    } as unknown as jest.Mocked<ApiRequestHandler>;

    service = new UserService({ apiDomain: domain, token });
    (ApiRequestHandler as jest.Mock).mockImplementation(() => apiHandler);
  });

  describe("constructor", () => {
    it("should initialize with default SSL verification", () => {
      new UserService({ apiDomain: domain, token });

      expect(ApiRequestHandler).toHaveBeenCalledWith({ apiDomain: domain, token });
    });

    it("should initialize with SSL verification disabled", () => {
      new UserService({ apiDomain: domain, token, verifySSL: false });

      expect(ApiRequestHandler).toHaveBeenCalledWith({
        apiDomain: domain,
        token,
        verifySSL: false,
      });
    });
  });

  describe("aboutMe", () => {
    it("should get current user profile", async () => {
      apiHandler.get.mockResolvedValue(mockUser);

      const result = await service.aboutMe();

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/user");
      expect(result).toEqual({
        user_id: mockUser.user_id,
        name: mockUser.name,
        username: mockUser.username,
        is_admin: mockUser.is_admin,
        applications: mockUser.applications,
        applications_admin: mockUser.applications_admin,
        picture: mockUser.picture,
        knowledge_bases: mockUser.knowledge_bases,
        email: ""
      });
    });

    it("should handle API errors", async () => {
      const error = new ApiError("Failed to fetch user profile");
      apiHandler.get.mockRejectedValue(error);

      await expect(service.aboutMe()).rejects.toThrow(error);
    });
  });

  describe("getData", () => {
    it("should get user data", async () => {
      apiHandler.get.mockResolvedValue(mockUserData);

      const result = await service.getData();

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/user/data");
      expect(result).toEqual(mockUserData);
    });

    it("should handle minimal user data", async () => {
      const minimalUserData: UserData = {
        user_id: "123",
      };

      apiHandler.get.mockResolvedValue(minimalUserData);

      const result = await service.getData();
      expect(result).toEqual(minimalUserData);
    });

    it("should handle empty user data", async () => {
      const emptyUserData: UserData = {};

      apiHandler.get.mockResolvedValue(emptyUserData);

      const result = await service.getData();
      expect(result).toEqual(emptyUserData);
    });

    it("should handle API errors", async () => {
      const error = new ApiError("Failed to fetch user data");
      apiHandler.get.mockRejectedValue(error);

      await expect(service.getData()).rejects.toThrow(error);
    });
  });

  describe("admin methods", () => {
    const base = "/v1/admin/users";

    it("listAdminUsers sends paging query and returns raw body", async () => {
      const page = { data: [{ id: "u1" }], pagination: { page: 0 } };
      apiHandler.get.mockResolvedValue(page);

      const result = await service.listAdminUsers();
      expect(apiHandler.get).toHaveBeenCalledWith(base, { page: 0, per_page: 20 });
      expect(result).toBe(page);
    });

    it("listAdminUsers includes search and filters", async () => {
      apiHandler.get.mockResolvedValue({ data: [], pagination: {} });

      await service.listAdminUsers(2, 5, "bob", '{"is_active":true}');
      expect(apiHandler.get).toHaveBeenCalledWith(base, {
        page: 2,
        per_page: 5,
        search: "bob",
        filters: '{"is_active":true}',
      });
    });

    it("getAdminUser GETs the encoded id", async () => {
      const user = { id: "a/b" };
      apiHandler.get.mockResolvedValue(user);

      const result = await service.getAdminUser("a/b");
      expect(apiHandler.get).toHaveBeenCalledWith(`${base}/a%2Fb`);
      expect(result).toBe(user);
    });

    it("updateAdminUser PUTs the fields", async () => {
      const user = { id: "u1", name: "N" };
      apiHandler.put.mockResolvedValue(user);

      const result = await service.updateAdminUser("a/b", { name: "N" });
      expect(apiHandler.put).toHaveBeenCalledWith(`${base}/a%2Fb`, { name: "N" });
      expect(result).toBe(user);
    });

    it("getUserProjects returns only the projects array", async () => {
      const projects = [{ project_name: "p", is_project_admin: false, is_default: true }];
      apiHandler.get.mockResolvedValue({ projects });

      const result = await service.getUserProjects("a/b");
      expect(apiHandler.get).toHaveBeenCalledWith(`${base}/a%2Fb/projects`);
      expect(result).toBe(projects);
    });

    it("assignUserToProject POSTs project and admin flag", async () => {
      apiHandler.post.mockResolvedValue({ ok: true });

      const result = await service.assignUserToProject("a/b", "p");
      expect(apiHandler.post).toHaveBeenCalledWith(`${base}/a%2Fb/projects`, {
        project_name: "p",
        is_project_admin: false,
      });
      expect(result).toEqual({ ok: true });
    });

    it("removeUserFromProject DELETEs encoded path and returns undefined", async () => {
      apiHandler.delete.mockResolvedValue({});

      const result = await service.removeUserFromProject("a/b", "my proj");
      expect(apiHandler.delete).toHaveBeenCalledWith(`${base}/a%2Fb/projects/my%20proj`);
      expect(result).toBeUndefined();
    });

    it("updateUserProjectRole PUTs flag and returns undefined", async () => {
      apiHandler.put.mockResolvedValue({});

      const result = await service.updateUserProjectRole("a/b", "p/q", true);
      expect(apiHandler.put).toHaveBeenCalledWith(`${base}/a%2Fb/projects/p%2Fq`, {
        is_project_admin: true,
      });
      expect(result).toBeUndefined();
    });

    it("setDefaultProject PUTs empty body and returns raw", async () => {
      apiHandler.put.mockResolvedValue({ ok: 1 });

      const result = await service.setDefaultProject("a/b", "p");
      expect(apiHandler.put).toHaveBeenCalledWith(`${base}/a%2Fb/projects/p/default`, {});
      expect(result).toEqual({ ok: 1 });
    });

    it("clearDefaultProject DELETEs default and returns raw", async () => {
      apiHandler.delete.mockResolvedValue({ ok: 2 });

      const result = await service.clearDefaultProject("a/b", "p");
      expect(apiHandler.delete).toHaveBeenCalledWith(`${base}/a%2Fb/projects/p/default`);
      expect(result).toEqual({ ok: 2 });
    });

    it("deactivateUser DELETEs and returns undefined", async () => {
      apiHandler.delete.mockResolvedValue({});

      const result = await service.deactivateUser("a/b");
      expect(apiHandler.delete).toHaveBeenCalledWith(`${base}/a%2Fb`);
      expect(result).toBeUndefined();
    });

    it("reactivateUser POSTs the reactivate route and returns the user", async () => {
      const user = { id: "u1", is_active: true };
      apiHandler.post.mockResolvedValue(user);

      const result = await service.reactivateUser("a/b");
      expect(apiHandler.post).toHaveBeenCalledWith(`${base}/a%2Fb/reactivate`);
      expect(result).toBe(user);
    });
  });
});
