import { type ProblemDetails, problemDetailsSchema } from '@shared/types/problem-details';

/**
 * The one error type the whole app deals with. Every failed request — network,
 * HTTP, or response-parsing — is normalized into an `ApiError` so UI code has a
 * single shape to render (DRY: see <ErrorState />).
 */
export class ApiError extends Error {
  readonly status: number;
  readonly problem?: ProblemDetails;
  readonly kind: 'network' | 'http' | 'parse';

  constructor(args: {
    message: string;
    status: number;
    kind: ApiError['kind'];
    problem?: ProblemDetails;
    cause?: unknown;
  }) {
    super(args.message, { cause: args.cause });
    this.name = 'ApiError';
    this.status = args.status;
    this.kind = args.kind;
    this.problem = args.problem;
  }

  /** Field-level validation messages, if the backend returned any. */
  get fieldErrors(): Record<string, string> {
    const out: Record<string, string> = {};
    for (const e of this.problem?.errors ?? []) {
      if (e.field) out[e.field] = e.message;
    }
    return out;
  }

  static async fromResponse(response: Response): Promise<ApiError> {
    let problem: ProblemDetails | undefined;
    try {
      const body: unknown = await response.json();
      const parsed = problemDetailsSchema.safeParse(body);
      if (parsed.success) problem = parsed.data;
    } catch {
      // response had no / invalid JSON body — fall back to status text
    }
    return new ApiError({
      message: problem?.title ?? `${response.status} ${response.statusText}`,
      status: response.status,
      kind: 'http',
      problem,
    });
  }
}
