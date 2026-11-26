import { describe, expect, it } from "@jest/globals";
import { HeadroomConfigSchema } from "../../../src/schemas/headroom";
import type {
  Assistant,
  HeadroomConfig,
  HeadroomOverride,
  HeadroomSavings,
  HistoryItem,
  TokensUsage,
  Workflow,
} from "../../../src/models";
import { HEADROOM_STRATEGY_VALUES } from "../../../src/models/headroom";
import { WorkflowMode } from "../../../src/models/workflow";

describe("HeadroomConfigSchema", () => {
  it("accepts a partial config", () => {
    expect(HeadroomConfigSchema.parse({ enabled: true })).toEqual({ enabled: true });
  });

  it("accepts every strategy literal", () => {
    for (const strategy of HEADROOM_STRATEGY_VALUES) {
      expect(HeadroomConfigSchema.parse({ strategy }).strategy).toBe(strategy);
    }
  });

  it("rejects an unknown strategy", () => {
    expect(() => HeadroomConfigSchema.parse({ strategy: "bogus" })).toThrow();
  });
});

describe("headroom model types", () => {
  it("compile on Assistant, Workflow, HistoryItem and TokensUsage", () => {
    const config: HeadroomConfig = {
      enabled: true,
      compress_user_messages: true,
      compress_tool_outputs: false,
      strategy: "lossless",
    };
    const override: HeadroomOverride = { strategy: "aggressive" };
    const savings: HeadroomSavings = {
      tokens_original: 100,
      tokens_compacted: 60,
      tokens_saved: 40,
      mode: "mixed",
      strategy: null,
      calls: 2,
    };
    const assistant: Pick<Assistant, "headroom_config"> = { headroom_config: config };
    const workflow: Pick<Workflow, "headroom_config" | "mode"> = {
      headroom_config: override,
      mode: WorkflowMode.SEQUENTIAL,
    };
    const history: Pick<HistoryItem, "headroom"> = { headroom: savings };
    const usage: TokensUsage = { headroom: savings };

    expect(assistant.headroom_config?.strategy).toBe("lossless");
    expect(workflow.headroom_config?.strategy).toBe("aggressive");
    expect(history.headroom?.mode).toBe("mixed");
    expect(usage.headroom?.calls).toBe(2);
  });
});
