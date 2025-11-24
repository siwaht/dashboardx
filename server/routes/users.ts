import { Router } from "express";
import { IStorage } from "../storage";
import { insertUserProfileSchema } from "../../shared/schema";

export function registerUserRoutes(router: Router, storage: IStorage) {
    const userRouter = Router();

    userRouter.get("/:tenantId", async (req, res) => {
        try {
            const users = await storage.getUsersByTenant(req.params.tenantId);
            res.json(users);
        } catch (error) {
            res.status(500).json({ error: error instanceof Error ? error.message : "Failed to fetch users" });
        }
    });

    userRouter.post("/", async (req, res) => {
        try {
            const data = insertUserProfileSchema.parse(req.body);
            const user = await storage.createUser(data);
            res.status(201).json(user);
        } catch (error) {
            res.status(400).json({ error: error instanceof Error ? error.message : "Invalid user data" });
        }
    });

    userRouter.patch("/:id", async (req, res) => {
        try {
            const user = await storage.updateUser(req.params.id, req.body);
            res.json(user);
        } catch (error) {
            res.status(400).json({ error: error instanceof Error ? error.message : "Failed to update user" });
        }
    });

    // Added DELETE route
    userRouter.delete("/:id", async (req, res) => {
        try {
            await storage.deleteUser(req.params.id);
            res.status(204).send();
        } catch (error) {
            res.status(500).json({ error: error instanceof Error ? error.message : "Failed to delete user" });
        }
    });

    router.use("/api/users", userRouter);
}
