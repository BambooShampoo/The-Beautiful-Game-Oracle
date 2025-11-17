import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse, server } from "../msw/server";
import { describe, expect, it, beforeEach } from "vitest";

import { PredictionDashboard } from "@/components/predict/prediction-dashboard";

describe("PredictionDashboard", () => {
  beforeEach(() => {
    server.resetHandlers();
  });

  it("shows manifest status and ensemble output", async () => {
    render(<PredictionDashboard />);
    expect(await screen.findByText(/Active Manifest/)).toBeInTheDocument();
    expect(await screen.findByText(/Ensemble method/)).toBeInTheDocument();
  });

  it("submits custom teams via combobox", async () => {
    server.use(
      http.post("/api/predict", async ({ request }) => {
        const body = await request.json();
        const homeCanonical = body.homeTeam;
        const homeName = homeCanonical === "liverpool" ? "Liverpool" : "Arsenal";
        return HttpResponse.json({
          ok: true,
          fixture: {
            season: "2023-2024",
            home: { name: homeName, shortName: "LIV" },
            away: { name: "Chelsea", shortName: "CHE" },
          },
          models: [
            {
              id: "performance_dense",
              format: "tfjs",
              location: { kind: "local", path: "/tmp/model.json" },
              probs: { home: 0.6, draw: 0.2, away: 0.2 },
              logits: { home: 0.5, draw: -0.3, away: -0.7 },
              note: "mock",
            },
          ],
          ensemble: {
            method: "avg",
            probs: { home: 0.6, draw: 0.2, away: 0.2 },
          },
        });
      }),
    );

    const user = userEvent.setup();
    render(<PredictionDashboard />);
    await screen.findByText(/Ensemble method/);

    const input = screen.getByLabelText(/Home team/i);
    await user.clear(input);
    await user.type(input, "Liverpool");
    await user.click(screen.getByRole("button", { name: /Run Prediction/i }));

    await waitFor(() =>
      expect(screen.getByText(/Liverpool vs Chelsea/)).toBeInTheDocument(),
    );
  });
});
