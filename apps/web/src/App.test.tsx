import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("App", () => {
  it("shows the resume ingestion workspace", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ status: "ok" }), { status: 200 }),
      )
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }));

    render(<App />);

    expect(
      screen.getByRole("heading", { name: /trusted career data/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/choose resume/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /job discovery/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /^applications$/i }),
    ).toBeInTheDocument();
    expect(await screen.findByText("Local service online")).toBeInTheDocument();
  });
});
