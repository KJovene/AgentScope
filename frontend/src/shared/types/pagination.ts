import { z } from 'zod';

/** Offset pagination — matches the backend contract (PLAN.md §5.3). */
export const paginationParamsSchema = z.object({
  limit: z.number().int().min(1).max(200).default(50),
  offset: z.number().int().min(0).default(0),
});
export type PaginationParams = z.infer<typeof paginationParamsSchema>;

/** Generic paginated envelope. Reused by every list endpoint (DRY). */
export const paginated = <T extends z.ZodTypeAny>(item: T) =>
  z.object({
    items: z.array(item),
    total: z.number().int().min(0),
    limit: z.number().int(),
    offset: z.number().int(),
  });

export type Paginated<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};
