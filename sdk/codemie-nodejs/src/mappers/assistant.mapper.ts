import type {
  AssistantCreateApiResponse,
  AssistantCreateResponse,
  BaseModelApiResponse,
  BaseModelResponse,
} from "../models";
import { omitUndefined } from "../utils/helpers";

export class AssistantMapper {
  static mapCreateResponse(response: AssistantCreateApiResponse): AssistantCreateResponse {
    const { assistant_id, ...rest } = response;
    const identifier = [assistant_id, response.assistantId, response.id].find(
      (value) => typeof value === "string" && value.trim().length > 0,
    );
    return { ...rest, ...(identifier ? { assistant_id: identifier.trim() } : {}) };
  }

  static mapBaseModelApiResponse(response: BaseModelApiResponse): BaseModelResponse {
    return omitUndefined({
      generated: response.generated,
      time_elapsed: response.timeElapsed,
      tokens_used: response.tokensUsed,
      thoughts: response.thoughts,
      task_id: response.taskId,
      success: response.success,
      agent_error: response.agentError,
      tool_errors: response.toolErrors,
    });
  }
}
