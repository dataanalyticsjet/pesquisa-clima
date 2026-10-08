import { AppShell } from "../components/layout/AppShell";
import { HeadContent, Scripts, createRootRoute } from "@tanstack/react-router";

import appCss from "../styles.css?url";

export const Route = createRootRoute({
  head: () => ({
    meta: [
      {
        charSet: "utf-8",
      },
      {
        name: "viewport",
        content: "width=device-width, initial-scale=1",
      },
      {
        title: "Pesquisa de Clima",
      },
      {
        name: "privacy-ui-deterrents",
        content: "enabled",
      },
    ],
    links: [
      {
        rel: "icon",
        type: "image/svg+xml",
        href: "/favicon.svg?v=2",
      },
      {
        rel: "stylesheet",
        href: appCss,
      },
    ],
  }),
  shellComponent: RootDocument,
});

function RootDocument({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <head>
        <HeadContent />
      </head>
      <body>
        <AppShell>{children}</AppShell>
        <Scripts />
      </body>
    </html>
  );
}
