import { jest, describe, expect, it, beforeEach } from "@jest/globals";
import { SkillService } from "../../../src/services/skill";
import { ApiRequestHandler } from "../../../src/utils/http";
import type {
  SkillCompanionFile,
  SkillCompanionFileMetadata,
  SkillCompanionFilePayload,
  SkillCreateParams,
  SkillVisibility,
} from "../../../src/models/skill";

jest.mock("../../../src/utils/http", () => ({
  ApiRequestHandler: jest.fn(),
}));

describe("SkillService", () => {
  const domain = "https://api.example.com";
  const token = "test-token";
  let service: SkillService;
  let apiHandler: jest.Mocked<ApiRequestHandler>;

  beforeEach(() => {
    apiHandler = {
      get: jest.fn(),
      post: jest.fn(),
      put: jest.fn(),
      delete: jest.fn(),
      stream: jest.fn(),
      request: jest.fn(),
      throwIfResponseError: jest.fn(),
    } as unknown as jest.Mocked<ApiRequestHandler>;

    (ApiRequestHandler as jest.Mock).mockImplementation(() => apiHandler);
    service = new SkillService({ apiDomain: domain, token });
  });

  describe("getConfig", () => {
    it("should get the platform skill limits from the config route", async () => {
      const config = { max_content_length: 30000, min_content_length: 100 };
      apiHandler.get.mockResolvedValueOnce(config);

      const result = await service.getConfig();

      expect(apiHandler.get).toHaveBeenCalledTimes(1);
      expect(apiHandler.get).toHaveBeenCalledWith("/v1/skills/config");
      expect(result).toEqual(config);
    });
  });

  describe("companion files", () => {
    const payload: SkillCompanionFilePayload[] = [
      { path: "docs/guide.md", content: "# Guide", encoding: "text" },
      {
        path: "assets/logo.png",
        content: "iVBORw0KGgo=",
        mime_type: "image/png",
        encoding: "base64",
        size_bytes: 8,
      },
    ];

    const metadata: SkillCompanionFileMetadata[] = [
      { path: "docs/guide.md", mime_type: "text/markdown", encoding: "text", size_bytes: 7 },
    ];

    it("should forward companion_files unchanged on create", async () => {
      const params: SkillCreateParams = {
        name: "my-skill",
        description: "A skill with companion files",
        content: "x".repeat(100),
        project: "demo",
        companion_files: payload,
      };
      apiHandler.post.mockResolvedValueOnce({ id: "s1" });

      await service.create(params);

      expect(apiHandler.post).toHaveBeenCalledWith("/v1/skills", params);
      expect(apiHandler.post.mock.calls[0][1]).toHaveProperty("companion_files", payload);
    });

    it("should forward companion_files unchanged on update", async () => {
      apiHandler.put.mockResolvedValueOnce({ id: "s1" });

      await service.update("s1", { companion_files: payload });

      expect(apiHandler.put).toHaveBeenCalledWith("/v1/skills/s1", { companion_files: payload });
    });

    it("should send null companion_files on update", async () => {
      apiHandler.put.mockResolvedValueOnce({ id: "s1" });

      await service.update("s1", { companion_files: null });

      expect(apiHandler.put).toHaveBeenCalledWith("/v1/skills/s1", { companion_files: null });
    });

    it("should leave companion_files absent on update when omitted", async () => {
      apiHandler.put.mockResolvedValueOnce({ id: "s1" });

      await service.update("s1", { description: "Updated description" });

      expect(apiHandler.put.mock.calls[0][1]).not.toHaveProperty("companion_files");
    });

    it("should list companion file metadata", async () => {
      apiHandler.get.mockResolvedValueOnce(metadata);

      const result = await service.listCompanionFiles("s1");

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/skills/s1/companion-files");
      expect(result).toEqual(metadata);
    });

    it("should get companion file content with the path as a query param", async () => {
      const file: SkillCompanionFile = {
        path: "docs/a b.md",
        mime_type: "text/markdown",
        encoding: "text",
        size_bytes: 7,
        content: "# Guide",
      };
      apiHandler.get.mockResolvedValueOnce(file);

      const result = await service.getCompanionFile("s1", "docs/a b.md");

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/skills/s1/companion-files/content", {
        path: "docs/a b.md",
      });
      expect(result).toEqual(file);
    });
  });

  describe("visibility", () => {
    const visibilities = ["project", "public"] as SkillVisibility[];

    it.each(visibilities)("create forwards visibility %s", async (visibility) => {
      const params: SkillCreateParams = {
        name: "my-skill",
        description: "A skill description",
        content: "c".repeat(100),
        project: "p",
        visibility,
      };
      apiHandler.post.mockResolvedValueOnce({});

      await service.create(params);

      expect(apiHandler.post).toHaveBeenCalledWith("/v1/skills", params);
      expect((apiHandler.post.mock.calls[0][1] as { visibility: string }).visibility).toBe(
        visibility,
      );
    });

    it.each(visibilities)("update forwards visibility %s", async (visibility) => {
      apiHandler.put.mockResolvedValueOnce({});

      await service.update("s1", { visibility });

      expect(apiHandler.put).toHaveBeenCalledWith("/v1/skills/s1", { visibility });
    });

    it.each(visibilities)("importSkill forwards visibility %s", async (visibility) => {
      const params = { file_content: "Zm9v", filename: "s.md", project: "p", visibility };
      apiHandler.post.mockResolvedValueOnce({});

      await service.importSkill(params);

      expect(apiHandler.post).toHaveBeenCalledWith("/v1/skills/import", params);
    });
  });
});
