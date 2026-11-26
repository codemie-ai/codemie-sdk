export const HEADROOM_STRATEGY_VALUES = ["lossless", "balanced", "aggressive"] as const;

export type HeadroomStrategy = (typeof HEADROOM_STRATEGY_VALUES)[number];

/** Headroom (token compression) settings stored on an assistant. LangGraphAgent runs only. */
export interface HeadroomConfig {
  enabled?: boolean;
  compress_user_messages?: boolean;
  compress_tool_outputs?: boolean;
  strategy?: HeadroomStrategy;
}

/** Partial Headroom settings, for example on a workflow. Same shape as HeadroomConfig. */
export type HeadroomOverride = HeadroomConfig;

/** Token savings reported for a message or an execution. */
export interface HeadroomSavings {
  tokens_original: number;
  tokens_compacted: number;
  tokens_saved: number;
  /** Open string: the backend may report modes the SDK does not know yet, e.g. "mixed". */
  mode: string;
  /** Open string, not HeadroomStrategy, so new backend strategies still parse. */
  strategy?: string | null;
  /** The backend defaults this to 1 when it omits the field. */
  calls?: number;
}
