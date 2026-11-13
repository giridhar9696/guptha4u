import { createRoot } from "react-dom/client"
import MeadowRiseFooter from "@/components/ui/meadow-rise-footer"

const mount = document.querySelector<HTMLElement>("[data-meadow-footer]")
if (mount) {
  const location = mount.querySelector(".footer-location")
  const store = {
    name: location?.querySelector("strong")?.textContent || "",
    address: location?.querySelector("span")?.textContent || "",
    phone: location?.querySelector("a")?.textContent || "",
    telephone: location?.querySelector("a")?.getAttribute("href") || "",
    map: location?.querySelector("a:last-child")?.getAttribute("href") || "",
  }
  createRoot(mount).render(<MeadowRiseFooter demoCheckout={mount.dataset.demoCheckout === "1"}
    department={document.body.dataset.department || "art"} store={store} />)
}
