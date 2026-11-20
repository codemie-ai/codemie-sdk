import { z } from "zod";

export const TIME_PERIOD_VALUES = [
  "last_hour",
  "last_6_hours",
  "last_24_hours",
  "last_7_days",
  "last_30_days",
  "last_60_days",
  "last_year",
] as const;

export type TimePeriod = (typeof TIME_PERIOD_VALUES)[number];

const timePeriodSchema = z.enum(TIME_PERIOD_VALUES);

const analyticsQueryParamsBase = z.object({
  time_period: timePeriodSchema.optional(),
  start_date: z.string().datetime({ offset: true }).optional(),
  end_date: z.string().datetime({ offset: true }).optional(),
  users: z.string().optional(),
  projects: z.string().optional(),
});

export const AnalyticsQueryParamsSchema = analyticsQueryParamsBase.readonly();

export type AnalyticsQueryParams = Partial<
  z.infer<typeof AnalyticsQueryParamsSchema>
>;

export const PaginatedAnalyticsQueryParamsSchema = analyticsQueryParamsBase
  .extend({
    page: z.number().int().min(0).default(0),
    per_page: z.number().int().min(1).default(20),
  })
  .readonly();

export type PaginatedAnalyticsQueryParams = Partial<
  z.infer<typeof PaginatedAnalyticsQueryParamsSchema>
>;

const attributesAnalyticsQueryParamsBase = analyticsQueryParamsBase.extend({
  page: z.number().int().min(0).default(0),
  per_page: z.number().int().min(1).default(20),
  /** One of: platform, ms-teams-bot, chrome_extension, other. */
  client_source: z.string().optional(),
  /** Run attributes filter; sent as a JSON string. All pairs must match. */
  attributes: z.record(z.string(), z.string()).optional(),
});

export const AttributesAnalyticsQueryParamsSchema = attributesAnalyticsQueryParamsBase.readonly();

export type AttributesAnalyticsQueryParams = Partial<
  z.infer<typeof AttributesAnalyticsQueryParamsSchema>
>;

export const AssistantsRequestsQueryParamsSchema = attributesAnalyticsQueryParamsBase
  .extend({
    assistant_id: z.string().optional(),
  })
  .readonly();

export type AssistantsRequestsQueryParams = Partial<
  z.infer<typeof AssistantsRequestsQueryParamsSchema>
>;

export const AttributesUsageQueryParamsSchema = attributesAnalyticsQueryParamsBase
  .extend({
    attribute_key: z.string(),
  })
  .readonly();

export type AttributesUsageQueryParams = z.input<typeof AttributesUsageQueryParamsSchema>;
