import { Router } from "express";
import { IStorage } from "../storage";
import { hashPassword, comparePasswords, createSession, deleteSession, getSession } from "../auth";
import { insertTenantSchema } from "../../shared/schema";
import { z } from "zod";

export function registerAuthRoutes(router: Router, storage: IStorage) {
    const authRouter = Router();

    authRouter.post("/signup", async (req, res) => {
        try {
            const { email, password, fullName, tenantName, invitationToken } = req.body;

            if (!email || !password) {
                return res.status(400).json({ error: "Email and password are required" });
            }

            // Check if user exists
            const existingUser = await storage.getUserByEmail(email);
            if (existingUser) {
                return res.status(400).json({ error: "User already exists" });
            }

            let tenantId: string;
            let role = "admin";
            let isActive = true;

            if (invitationToken) {
                // Handle invitation logic here (to be implemented with storage method)
                // For now, we'll assume the token is valid and get the tenantId from it
                // This requires implementing getInvitationByToken in storage
                // const invitation = await storage.getInvitationByToken(invitationToken);
                // if (!invitation || invitation.status !== 'pending') ...
                // tenantId = invitation.tenantId;
                // role = invitation.role;

                // Placeholder until storage method exists
                return res.status(501).json({ error: "Invitation signup not yet implemented" });
            } else {
                // Create new tenant
                const tenant = await storage.createTenant({
                    name: tenantName || `${email}'s Organization`,
                    settings: {}
                });
                tenantId = tenant.id;
            }

            // Hash password and create user
            const hashedPassword = await hashPassword(password);
            const user = await storage.createUser({
                id: crypto.randomUUID(),
                tenantId,
                email,
                fullName: fullName || null,
                role,
                isActive,
                passwordHash: hashedPassword
            });

            // Create session
            const sessionId = createSession(user.id, tenantId);

            res.status(201).json({
                user: {
                    id: user.id,
                    email: user.email,
                    fullName: user.fullName,
                    role: user.role,
                    tenantId: user.tenantId,
                    isActive: user.isActive
                },
                session: { access_token: sessionId }
            });
        } catch (error) {
            console.error("Signup error:", error);
            res.status(500).json({ error: error instanceof Error ? error.message : "Failed to create account" });
        }
    });

    authRouter.post("/signin", async (req, res) => {
        try {
            const { email, password } = req.body;

            if (!email || !password) {
                return res.status(400).json({ error: "Email and password are required" });
            }

            // Get user
            const user = await storage.getUserByEmail(email);
            if (!user || !user.passwordHash) {
                return res.status(401).json({ error: "Invalid credentials" });
            }

            // Verify password
            const isValid = await comparePasswords(password, user.passwordHash);
            if (!isValid) {
                return res.status(401).json({ error: "Invalid credentials" });
            }

            // Create session
            const sessionId = createSession(user.id, user.tenantId);

            res.json({
                user: {
                    id: user.id,
                    email: user.email,
                    fullName: user.fullName,
                    role: user.role,
                    tenantId: user.tenantId,
                    isActive: user.isActive
                },
                session: { access_token: sessionId }
            });
        } catch (error) {
            console.error("Signin error:", error);
            res.status(500).json({ error: error instanceof Error ? error.message : "Failed to sign in" });
        }
    });

    authRouter.post("/signout", (req, res) => {
        const token = req.headers.authorization?.replace("Bearer ", "");
        if (token) {
            deleteSession(token);
        }
        res.json({ message: "Signed out successfully" });
    });

    authRouter.get("/session", async (req, res) => {
        try {
            const token = req.headers.authorization?.replace("Bearer ", "");
            if (!token) {
                return res.status(401).json({ error: "No token provided" });
            }

            const session = getSession(token);
            if (!session) {
                return res.status(401).json({ error: "Invalid or expired session" });
            }

            const user = await storage.getUserById(session.userId);

            if (!user) {
                return res.status(404).json({ error: "User not found" });
            }

            res.json({
                user: {
                    id: user.id,
                    email: user.email,
                    fullName: user.fullName,
                    role: user.role,
                    tenantId: user.tenantId,
                    isActive: user.isActive
                }
            });
        } catch (error) {
            res.status(500).json({ error: error instanceof Error ? error.message : "Failed to get session" });
        }
    });

    router.use("/api/auth", authRouter);
}
