import { Router } from "express";
import { IStorage } from "../storage";
import { insertChatSessionSchema, insertChatMessageSchema } from "../../shared/schema";

export function registerChatRoutes(router: Router, storage: IStorage) {
    const chatRouter = Router();

    chatRouter.get("/sessions/:userId", async (req, res) => {
        try {
            const sessions = await storage.getChatSessions(req.params.userId);
            res.json(sessions);
        } catch (error) {
            res.status(500).json({ error: error instanceof Error ? error.message : "Failed to fetch chat sessions" });
        }
    });

    chatRouter.get("/sessions/:id/messages", async (req, res) => {
        try {
            const messages = await storage.getChatMessages(req.params.id);
            res.json(messages);
        } catch (error) {
            res.status(500).json({ error: error instanceof Error ? error.message : "Failed to fetch messages" });
        }
    });

    chatRouter.post("/sessions", async (req, res) => {
        try {
            const data = insertChatSessionSchema.parse(req.body);
            const session = await storage.createChatSession(data);
            res.status(201).json(session);
        } catch (error) {
            res.status(400).json({ error: error instanceof Error ? error.message : "Invalid session data" });
        }
    });

    chatRouter.post("/messages", async (req, res) => {
        try {
            const data = insertChatMessageSchema.parse(req.body);
            const message = await storage.createChatMessage(data);
            res.status(201).json(message);
        } catch (error) {
            res.status(400).json({ error: error instanceof Error ? error.message : "Invalid message data" });
        }
    });

    chatRouter.delete("/sessions/:id", async (req, res) => {
        try {
            await storage.deleteChatSession(req.params.id);
            res.status(204).send();
        } catch (error) {
            res.status(500).json({ error: error instanceof Error ? error.message : "Failed to delete session" });
        }
    });

    router.use("/api/chat", chatRouter);
}
