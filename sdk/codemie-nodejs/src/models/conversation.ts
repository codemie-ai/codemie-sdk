export interface Conversation {
  id: string;
  name: string;
  folder?: string;
  pinned: boolean;
  date: string;
  assistant_ids: string[];
  initial_assistant_id?: string;
}

export interface Mark {
  mark: string;
  rating: number;
  comments: string;
  date: string;
  operator?: Operator;
}

export interface Operator {
  user_id: string;
  name: string;
}

export interface Thought {
  id: string;
  parent_id?: string;
  metadata: Record<string, unknown>;
  in_progress: boolean;
  input_text?: string;
  message?: string;
  author_type: string;
  author_name: string;
  output_format: string;
  error?: boolean;
  children: string[];
}

export interface HistoryMark {
  mark: string;
  rating: number;
  comments?: string;
  date: string;
}

export interface HistoryItem {
  role: string;
  message: string;
  historyIndex: number;
  date: string;
  responseTime?: number;
  inputTokens?: number;
  outputTokens?: number;
  moneySpent?: number;
  userMark?: HistoryMark;
  operatorMark?: HistoryMark;
  messageRaw?: string;
  fileNames: string[];
  assistantId?: string;
  thoughts?: Thought[];
}

export interface ContextItem {
  context_type?: "knowledge_base" | "code" | "provider";
  name: string;
}

export interface ToolItem {
  name: string;
  label?: string;
  settings_config?: boolean;
  user_description?: string;
}

export interface AssistantDataItem {
  assistant_id: string;
  assistant_name: string;
  assistant_icon?: string;
  assistant_type: string;
  context: (ContextItem | string)[];
  tools: ToolItem[];
  conversation_starters: string[];
  hide_tool_outputs?: boolean;
}

export interface ConversationDetailsData {
  llm_model?: string;
  context: ContextItem[];
  app_name?: string;
  repo_name?: string;
  index_type?: string;
}

export interface AssistantDetailsData {
  assistant_id: string;
  assistant_name: string;
  assistant_icon: string;
  assistant_type: string;
  context: (ContextItem | string)[];
  tools: ToolItem[];
  conversation_starters: string[];
  hide_tool_outputs?: boolean;
}

export interface ConversationDetails {
  id: string;
  date: string;
  update_date: string;
  conversation_id: string;
  conversation_name: string;
  llm_model?: string;
  folder?: string;
  pinned: boolean;
  history: HistoryItem[];
  user_id: string;
  user_name: string;
  assistant_ids: string[];
  assistant_data: AssistantDataItem[];
  initial_assistant_id: string;
  final_user_mark?: Mark;
  final_operator_mark?: Mark;
  project: string;
  conversation_details?: ConversationDetailsData;
  assistant_details?: AssistantDetailsData;
  user_abilities?: string[];
  is_folder_migrated: boolean;
  category?: string;
  mcp_server_single_usage?: boolean;
}

export interface ConversationCreateRequest {
  initial_assistant_id?: string;
  folder?: string;
  mcp_server_single_usage?: boolean;
}
