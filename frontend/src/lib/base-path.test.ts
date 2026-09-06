import { describe, expect, it } from "vitest";

import { withBase } from "./base-path";

describe("withBase", () => {
  it("puts the deployment's base path in front of a site-root path", () => {
    // PAGES_BASE_PATH is read once at import; locally it is empty, so the path is
    // root-relative, which is what makes it correct from any depth.
    expect(withBase("data/feed.xml")).toMatch(/^\/.*data\/feed\.xml$/);
    expect(withBase("/data/feed.xml")).toBe(withBase("data/feed.xml"));
  });
});
