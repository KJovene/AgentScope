// Standalone TanStack Router codegen. `routeTree.gen.ts` is gitignored (it is
// derived from src/app/routes/**) and is normally produced as a side effect of
// `vite dev` / `vite build` via the plugin in vite.config.ts. `tsc` does not run
// Vite, so a clean checkout (CI) has no route tree before typecheck/test/build —
// this script produces it standalone, from the same tsr.config.json. Wired as a
// `pre*` npm hook on typecheck/test/build so it always runs first.
import { Generator, getConfig } from '@tanstack/router-generator';

const config = getConfig({}, process.cwd());
const generator = new Generator({ config, root: process.cwd() });
await generator.run();
