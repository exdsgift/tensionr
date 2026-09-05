/**
 * Placeholder homepage.
 *
 * This exists so that #81 can land without taking the site down. `assemble-site.sh`
 * refuses to publish a tree with no homepage — it keeps the last good deployment live
 * instead — so a structural pull request that removed the old generator and shipped
 * nothing in its place would freeze production and leave every branch preview
 * homepage-less, losing previews exactly when #82 needs them to review a redesign.
 *
 * Deliberately unstyled beyond what `shadcn init` provides, and deliberately honest
 * about being a placeholder. It is replaced wholesale by #82.
 */
export default function Home() {
  return (
    <main className="mx-auto flex min-h-full w-full max-w-2xl flex-col justify-center gap-6 px-6 py-16">
      <header className="flex flex-col gap-2">
        <h1 className="font-mono text-2xl font-semibold tracking-tight">tensionr</h1>
        <p className="text-muted-foreground text-balance">
          Not the world&rsquo;s tension — the disagreement between those who narrate it.
        </p>
      </header>

      <div className="border-border bg-card text-card-foreground rounded-lg border p-6">
        <h2 className="mb-2 font-medium">The interface is being rebuilt</h2>
        <p className="text-muted-foreground text-sm">
          The engine still runs, and every window it measures is still published as
          data. The page that reads it is being replaced; this placeholder stands in
          until it lands.
        </p>
      </div>

      <p className="text-muted-foreground text-sm">
        The measurements are in{" "}
        <a
          className="underline underline-offset-4 hover:no-underline"
          href="data/stories.json"
        >
          data/stories.json
        </a>
        , which is the same file the page reads and needs nothing from this site to be
        useful.
      </p>

      <footer className="text-muted-foreground mt-4 text-xs">
        <a
          className="underline underline-offset-4 hover:no-underline"
          href="https://github.com/exdsgift/tensionr"
          rel="nofollow noopener"
        >
          github.com/exdsgift/tensionr
        </a>
      </footer>
    </main>
  );
}
