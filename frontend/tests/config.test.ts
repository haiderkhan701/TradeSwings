import { describe, expect, it } from "vitest";

import { getApiBaseUrl } from "../lib/config";

describe("frontend config", () => {
  it("provides an API base URL", () => {
    expect(getApiBaseUrl()).toMatch(/^https?:\/\//);
  });
});
