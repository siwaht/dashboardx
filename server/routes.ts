import type { Express, Request, Response, NextFunction } from "express";
import type { IStorage } from "./storage.js";
import { registerAuthRoutes } from "./routes/auth.js";
import { registerUserRoutes } from "./routes/users.js";
import { registerDocumentRoutes } from "./routes/documents.js";
import { registerChatRoutes } from "./routes/chat.js";
import { registerInvitationRoutes } from "./routes/invitations.js";

export function registerRoutes(app: Express, storage: IStorage) {

  // Health check
  app.get("/api/health", (_req, res) => {
    res.json({ status: "ok", timestamp: new Date().toISOString() });
  });

  // Register modular routes
  registerAuthRoutes(app, storage);
  registerUserRoutes(app, storage);
  registerDocumentRoutes(app, storage);
  registerChatRoutes(app, storage);
  registerInvitationRoutes(app, storage);
}
