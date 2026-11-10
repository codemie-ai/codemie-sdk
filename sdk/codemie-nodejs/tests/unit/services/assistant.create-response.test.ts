import { describe, expect, it, jest } from "@jest/globals";
import { AssistantService } from "../../../src/services/assistant";
import { ApiRequestHandler } from "../../../src/utils/http";
import type { AssistantCreateParams } from "../../../src/schemas";

jest.mock("../../../src/utils/http", () => ({ ApiRequestHandler: jest.fn() }));

const params: AssistantCreateParams = {
  name: "Example Assistant", description: "An example assistant", project: "example-project",
  system_prompt: "Example", llm_model_type: "gpt-4o", toolkits: [], context: [],
  conversation_starters: [], mcp_servers: [], assistant_ids: [], prompt_variables: [],
};

describe("assistant create response normalization", () => {
  it.each(["assistantId", "assistant_id", "id"])("normalizes %s", async (key) => {
    const post = jest.fn<() => Promise<unknown>>().mockResolvedValue({ message: "Saved", [key]: " example-id " });
    (ApiRequestHandler as jest.Mock).mockImplementation(() => ({ post }));
    const service = new AssistantService({ apiDomain: "https://api.example.com" });
    await expect(service.create(params)).resolves.toMatchObject({ message: "Saved", assistant_id: "example-id" });
  });

  it("skips blank aliases and preserves validation details when no ID was created", async () => {
    const response = {
      message: "Please configure integrations",
      assistantId: null,
      validation: { has_missing_integrations: true, missing_by_credential_type: [], sub_assistants_missing: [] },
    };
    const post = jest.fn<() => Promise<unknown>>().mockResolvedValue(response);
    (ApiRequestHandler as jest.Mock).mockImplementation(() => ({ post }));
    const service = new AssistantService({ apiDomain: "https://api.example.com" });
    await expect(service.create(params)).resolves.toMatchObject({ message: response.message, validation: response.validation });
    post.mockResolvedValue({ message: "Saved", assistant_id: " ", assistantId: "canonical-id" });
    await expect(service.create(params)).resolves.toMatchObject({ assistant_id: "canonical-id" });
  });
});
