import { Router } from "express";
import { IStorage } from "../storage";
import { insertInvitationSchema } from "../../shared/schema";
import { randomBytes } from "crypto";

export function registerInvitationRoutes(router: Router, storage: IStorage) {
    const inviteRouter = Router();

    // Create invitation (Admin only)
    inviteRouter.post("/", async (req, res) => {
        try {
            // TODO: Add admin check middleware here

            const { email, role, tenantId, invitedBy } = req.body;

            const token = randomBytes(32).toString("hex");
            const expiresAt = new Date();
            expiresAt.setDate(expiresAt.getDate() + 7); // 7 days expiry

            // We need to implement createInvitation in storage
            const invitation = await storage.createInvitation({
                email,
                role,
                tenantId,
                invitedBy,
                token,
                expiresAt,
                status: 'pending'
            });

            res.status(201).json(invitation);
        } catch (error) {
            res.status(400).json({ error: error instanceof Error ? error.message : "Failed to create invitation" });
        }
    });

    // Get invitation by token (Public)
    inviteRouter.get("/:token", async (req, res) => {
        try {
            const invitation = await storage.getInvitationByToken(req.params.token);
            if (!invitation) {
                return res.status(404).json({ error: "Invitation not found" });
            }
            if (new Date() > invitation.expiresAt) {
                return res.status(410).json({ error: "Invitation expired" });
            }
            res.json(invitation);
        } catch (error) {
            res.status(500).json({ error: error instanceof Error ? error.message : "Failed to fetch invitation" });
        }
    });

    router.use("/api/invitations", inviteRouter);
}
