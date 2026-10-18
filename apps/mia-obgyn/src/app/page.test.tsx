import { render, screen } from "@testing-library/react";
import HomePage from "./page";

describe("Mia OB-GYN app shell", () => {
  it("shows synthetic-only status and OB-GYN navigation", () => {
    render(<HomePage />);
    expect(screen.getByText(/prototype · synthetic data only/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /patients/i })).toHaveAttribute("href", "/patients");
    expect(screen.getByRole("link", { name: /appointments/i })).toHaveAttribute("href", "/appointments");
    expect(screen.getByRole("link", { name: /evidence library/i })).toHaveAttribute("href", "/evidence");
    expect(screen.queryByRole("link", { name: /dental/i })).not.toBeInTheDocument();
  });
});
