import { render, screen } from "@testing-library/react";
import RootLayout from "./layout";
describe("Mia OB-GYN document shell",()=>{it("renders the app with its title and language",()=>{const view=render(<RootLayout><div>Prototype · Synthetic data only</div></RootLayout>);expect(view.container.querySelector("html")).toHaveAttribute("lang","en");expect(screen.getByText(/synthetic data only/i)).toBeInTheDocument();});});
