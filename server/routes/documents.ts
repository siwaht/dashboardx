import { Router } from "express";
import { IStorage } from "../storage";
import { insertDocumentSchema } from "../../shared/schema";

export function registerDocumentRoutes(router: Router, storage: IStorage) {
    const docRouter = Router();

    docRouter.get("/:tenantId", async (req, res) => {
        try {
            const documents = await storage.getDocuments(req.params.tenantId);
            res.json(documents);
        } catch (error) {
            res.status(500).json({ error: error instanceof Error ? error.message : "Failed to fetch documents" });
        }
    });

    docRouter.post("/", async (req, res) => {
        try {
            const data = insertDocumentSchema.parse(req.body);
            const document = await storage.createDocument(data);
            res.status(201).json(document);
        } catch (error) {
            res.status(400).json({ error: error instanceof Error ? error.message : "Invalid document data" });
        }
    });

    docRouter.patch("/:id", async (req, res) => {
        try {
            const document = await storage.updateDocument(req.params.id, req.body);
            res.json(document);
        } catch (error) {
            res.status(400).json({ error: error instanceof Error ? error.message : "Failed to update document" });
        }
    });

    docRouter.delete("/:id", async (req, res) => {
        try {
            await storage.deleteDocument(req.params.id);
            res.status(204).send();
        } catch (error) {
            res.status(500).json({ error: error instanceof Error ? error.message : "Failed to delete document" });
        }
    });

    router.use("/api/documents", docRouter);
}
