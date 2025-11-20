import "@testing-library/jest-dom/vitest";
import "whatwg-fetch";

import { afterAll, afterEach, beforeAll, beforeEach, vi } from "vitest";

import { server } from "./tests/msw/server";

beforeEach(() => {
  vi.restoreAllMocks();
  vi.resetModules();
});

afterEach(() => {
  vi.clearAllMocks();
});

beforeAll(() => {
  server.listen({ onUnhandledRequest: "error" });
});

afterEach(() => {
  server.resetHandlers();
});

afterAll(() => {
  server.close();
});
