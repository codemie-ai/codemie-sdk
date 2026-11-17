import { z } from "zod";
import { HEADROOM_STRATEGY_VALUES } from "../models/headroom";

export const HeadroomConfigSchema = z.object({
  enabled: z.boolean().optional(),
  compress_user_messages: z.boolean().optional(),
  compress_tool_outputs: z.boolean().optional(),
  strategy: z.enum(HEADROOM_STRATEGY_VALUES).optional(),
});
