import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { TeamSelect } from "@/components/predict/team-select";

describe("TeamSelect", () => {
  it("renders crest preview", () => {
    const handleChange = vi.fn();
    render(
      <TeamSelect
        label="Home team"
        value="arsenal"
        onChange={handleChange}
      />,
    );
    expect(screen.getByLabelText("Home team")).toBeInTheDocument();
    expect(screen.getByAltText(/Arsenal crest/i)).toBeInTheDocument();
  });

  it("searches and selects via user input", async () => {
    const handleChange = vi.fn();
    render(
      <TeamSelect
        label="Home"
        value="arsenal"
        onChange={handleChange}
      />,
    );
    const input = screen.getByLabelText("Home");
    const user = userEvent.setup();
    await user.clear(input);
    await user.type(input, "Chelsea");
    expect(handleChange).toHaveBeenCalledWith("chelsea");
  });
});
