import express, { type Express } from "express";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { createServer as createViteServer } from "vite";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export async function setupVite(app: Express, server: any) {
  if (process.env.NODE_ENV === "production") {
    const distPath = path.resolve(__dirname, "../dist/public");
    app.use(express.static(distPath));
    app.use((_req, res, next) => {
      if (_req.path.startsWith("/api")) {
        return next();
      }
      res.sendFile(path.resolve(distPath, "index.html"));
    });
  } else {
    const vite = await createViteServer({
      server: {
        middlewareMode: true,
        hmr: { server },
      },
      appType: "custom",
    });

    app.use(vite.middlewares);
    app.use(async (req, res, next) => {
      if (req.originalUrl.startsWith("/api")) {
        return next();
      }

      try {
        const template = fs.readFileSync(
          path.resolve(__dirname, "../client/index.html"),
          "utf-8",
        );
        const page = await vite.transformIndexHtml(req.originalUrl, template);
        res.status(200).set({ "Content-Type": "text/html" }).end(page);
      } catch (e) {
        if (e instanceof Error) {
          vite.ssrFixStacktrace(e);
        }
        next(e);
      }
    });
  }
}
