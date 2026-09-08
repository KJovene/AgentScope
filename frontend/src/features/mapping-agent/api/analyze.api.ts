import { http } from '@shared/api/http-client';

import { type AnalyzeFileInput, analyzeResultSchema } from './analyze.contracts';

/**
 * Thin transport layer: build the request, delegate parsing/errors to `http`.
 * `/analyze` creates no resource — a single file in, an ephemeral result out.
 */
export const analyzeApi = {
  analyze: (input: AnalyzeFileInput) => {
    const formData = new FormData();
    formData.append('file', input.file, input.file.name);
    return http.post('/analyze', analyzeResultSchema, { formData });
  },
};
