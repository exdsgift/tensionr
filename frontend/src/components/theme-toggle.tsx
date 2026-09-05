"use client";

/**
 * Three states, not two: follow the system, force light, force dark.
 *
 * Two-state toggles have to guess what "off" means on a machine set to dark, and they
 * get it wrong for exactly the readers who care most. Following the system is the
 * default and stays reachable, so a choice made once is not a choice made forever.
 *
 * The CSS does the work. `prefers-color-scheme` supplies the palette when no class is
 * present, and `.light` / `.dark` on the root override it. So this component only ever
 * sets or clears a class, and with scripting off the page still follows the system.
 *
 * The flash is prevented in `layout.tsx`, by a script that runs before first paint.
 * This component only handles the click.
 *
 * The stored choice is read through `useSyncExternalStore` rather than an effect. That
 * is the API for a value which only exists on the client, it keeps the linter's
 * cascading-render rule satisfied, and it syncs two open tabs for free.
 */

import { useSyncExternalStore } from "react";
import { Monitor, Moon, Sun } from "lucide-react";

type Choice = "system" | "light" | "dark";

const KEY = "tensionr-theme";
const ORDER: Choice[] = ["system", "light", "dark"];
const LABEL: Record<Choice, string> = {
  system: "Theme: following your system",
  light: "Theme: light",
  dark: "Theme: dark",
};

function apply(choice: Choice) {
  const root = document.documentElement;
  root.classList.remove("light", "dark");
  if (choice !== "system") root.classList.add(choice);
  try {
    if (choice === "system") localStorage.removeItem(KEY);
    else localStorage.setItem(KEY, choice);
  } catch {
    // Private mode, or storage disabled. The class is still set, so the choice holds
    // for this page; it simply will not be remembered. That is a smaller failure than
    // not switching at all.
  }
}

function subscribe(onChange: () => void) {
  // `storage` fires in the *other* tabs, so a choice made in one follows into the rest.
  // The click path updates this tab directly.
  window.addEventListener("storage", onChange);
  window.addEventListener("tensionr-theme", onChange);
  return () => {
    window.removeEventListener("storage", onChange);
    window.removeEventListener("tensionr-theme", onChange);
  };
}

function read(): Choice {
  try {
    const stored = localStorage.getItem(KEY);
    return stored === "light" || stored === "dark" ? stored : "system";
  } catch {
    return "system";
  }
}

export function ThemeToggle() {
  // The server has no storage to read, so it renders the default. The pre-paint script
  // in layout.tsx has already applied any stored class by then, so the page is never
  // the wrong colour; only this button is briefly the wrong icon.
  const choice = useSyncExternalStore(subscribe, read, () => "system" as Choice);

  const next = ORDER[(ORDER.indexOf(choice) + 1) % ORDER.length];
  const Icon = choice === "system" ? Monitor : choice === "light" ? Sun : Moon;

  return (
    <button
      type="button"
      className="theme-toggle"
      aria-label={`${LABEL[choice]}. Activate for ${LABEL[next].toLowerCase()}`}
      title={LABEL[choice]}
      onClick={() => {
        apply(next);
        window.dispatchEvent(new Event("tensionr-theme"));
      }}
    >
      <Icon aria-hidden="true" />
    </button>
  );
}
