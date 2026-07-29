import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("App", () => {
  it("shows the local foundation", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ status: "ok" }), { status: 200 }),
    );

    render(<App />);

    expect(
      screen.getByRole("heading", { name: /job application workspace/i }),
    ).toBeInTheDocument();
    expect(await screen.findByText("Local service online")).toBeInTheDocument();
  });
});
