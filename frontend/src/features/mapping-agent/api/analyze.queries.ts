import { useMutation } from '@tanstack/react-query';

import { analyzeApi } from './analyze.api';
import { type AnalyzeFileInput } from './analyze.contracts';

/** Server-state hook. Components use this, never `analyzeApi` directly. */
export function useAnalyzeMutation() {
  return useMutation({
    mutationFn: (input: AnalyzeFileInput) => analyzeApi.analyze(input),
  });
}
