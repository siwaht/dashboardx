import type { Express, Request, Response, NextFunction } from "express";
import type { IStorage } from "./storage.js";
import {
  insertUserProfileSchema,
  insertDocumentSchema,
  insertChatSessionSchema,
  insertChatMessageSchema,
  insertDataSourceSchema,
  insertCustomAgentSchema,
  insertAgentExecutionSchema,
  insertTenantSchema
} from "../shared/schema.js";
import { hashPassword, comparePasswords, createSession, getSession, deleteSession } from "./auth.js";

// Middleware to check authentication
function requireAuth(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization;
  const token = authHeader?.replace("Bearer ", "");
  
  if (!token) {
    return res.status(401).json({ error: "Unauthorized - No token provided" });
  }
  
  const session = getSession(token);
  if (!session) {
    return res.status(401).json({ error: "Unauthorized - Invalid or expired session" });
  }
  
  (req as any).session = session;
  next();
}

export function registerRoutes(app: Express, storage: IStorage) {
  
  // Health check
  app.get("/api/health", (_req, res) => {
    res.json({ status: "ok", timestamp: new Date().toISOString() });
  });

  // Auth routes
  app.post("/api/auth/signup", async (req, res) => {
    try {
      const { email, password, fullName, tenantName } = req.body;
      
      if (!email || !password) {
        return res.status(400).json({ error: "Email and password are required" });
      }
      
      // Check if user exists
      const existingUser = await storage.getUserByEmail(email);
      if (existingUser) {
        return res.status(400).json({ error: "User already exists" });
      }
      
      // Create tenant
      const tenant = await storage.createTenant({
        name: tenantName || `${email}'s Organization`,
        settings: {}
      });
      
      // Hash password and create user
      const hashedPassword = await hashPassword(password);
      const user = await storage.createUser({
        id: crypto.randomUUID(),
        tenantId: tenant.id,
        email,
        fullName: fullName || null,
        role: "admin",
        isActive: true,
        passwordHash: hashedPassword
      });
      
      // Create session
      const sessionId = createSession(user.id, tenant.id);
      
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

  app.post("/api/auth/signin", async (req, res) => {
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

  app.post("/api/auth/signout", requireAuth, (req, res) => {
    const token = req.headers.authorization?.replace("Bearer ", "");
    if (token) {
      deleteSession(token);
    }
    res.json({ message: "Signed out successfully" });
  });

  app.get("/api/auth/session", requireAuth, async (req, res) => {
    try {
      const session = (req as any).session;
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

  // User routes
  app.get("/api/users/:tenantId", async (req, res) => {
    try {
      const users = await storage.getUsersByTenant(req.params.tenantId);
      res.json(users);
    } catch (error) {
      res.status(500).json({ error: error instanceof Error ? error.message : "Failed to fetch users" });
    }
  });

  app.post("/api/users", async (req, res) => {
    try {
      const data = insertUserProfileSchema.parse(req.body);
      const user = await storage.createUser(data);
      res.status(201).json(user);
    } catch (error) {
      res.status(400).json({ error: error instanceof Error ? error.message : "Invalid user data" });
    }
  });

  app.patch("/api/users/:id", async (req, res) => {
    try {
      const user = await storage.updateUser(req.params.id, req.body);
      res.json(user);
    } catch (error) {
      res.status(400).json({ error: error instanceof Error ? error.message : "Failed to update user" });
    }
  });

  // Document routes
  app.get("/api/documents/:tenantId", async (req, res) => {
    try {
      const documents = await storage.getDocuments(req.params.tenantId);
      res.json(documents);
    } catch (error) {
      res.status(500).json({ error: error instanceof Error ? error.message : "Failed to fetch documents" });
    }
  });

  app.post("/api/documents", async (req, res) => {
    try {
      const data = insertDocumentSchema.parse(req.body);
      const document = await storage.createDocument(data);
      res.status(201).json(document);
    } catch (error) {
      res.status(400).json({ error: error instanceof Error ? error.message : "Invalid document data" });
    }
  });

  app.patch("/api/documents/:id", async (req, res) => {
    try {
      const document = await storage.updateDocument(req.params.id, req.body);
      res.json(document);
    } catch (error) {
      res.status(400).json({ error: error instanceof Error ? error.message : "Failed to update document" });
    }
  });

  app.delete("/api/documents/:id", async (req, res) => {
    try {
      await storage.deleteDocument(req.params.id);
      res.status(204).send();
    } catch (error) {
      res.status(500).json({ error: error instanceof Error ? error.message : "Failed to delete document" });
    }
  });

  // Chat session routes
  app.get("/api/chat/sessions/:userId", async (req, res) => {
    try {
      const sessions = await storage.getChatSessions(req.params.userId);
      res.json(sessions);
    } catch (error) {
      res.status(500).json({ error: error instanceof Error ? error.message : "Failed to fetch chat sessions" });
    }
  });

  app.get("/api/chat/sessions/:id/messages", async (req, res) => {
    try {
      const messages = await storage.getChatMessages(req.params.id);
      res.json(messages);
    } catch (error) {
      res.status(500).json({ error: error instanceof Error ? error.message : "Failed to fetch messages" });
    }
  });

  app.post("/api/chat/sessions", async (req, res) => {
    try {
      const data = insertChatSessionSchema.parse(req.body);
      const session = await storage.createChatSession(data);
      res.status(201).json(session);
    } catch (error) {
      res.status(400).json({ error: error instanceof Error ? error.message : "Invalid session data" });
    }
  });

  app.post("/api/chat/messages", async (req, res) => {
    try {
      const data = insertChatMessageSchema.parse(req.body);
      const message = await storage.createChatMessage(data);
      res.status(201).json(message);
    } catch (error) {
      res.status(400).json({ error: error instanceof Error ? error.message : "Invalid message data" });
    }
  });

  app.delete("/api/chat/sessions/:id", async (req, res) => {
    try {
      await storage.deleteChatSession(req.params.id);
      res.status(204).send();
    } catch (error) {
      res.status(500).json({ error: error instanceof Error ? error.message : "Failed to delete session" });
    }
  });

  // Data source routes
  app.get("/api/data-sources/:tenantId", async (req, res) => {
    try {
      const dataSources = await storage.getDataSources(req.params.tenantId);
      res.json(dataSources);
    } catch (error) {
      res.status(500).json({ error: error instanceof Error ? error.message : "Failed to fetch data sources" });
    }
  });

  app.post("/api/data-sources", async (req, res) => {
    try {
      const data = insertDataSourceSchema.parse(req.body);
      const dataSource = await storage.createDataSource(data);
      res.status(201).json(dataSource);
    } catch (error) {
      res.status(400).json({ error: error instanceof Error ? error.message : "Invalid data source" });
    }
  });

  app.patch("/api/data-sources/:id", async (req, res) => {
    try {
      const dataSource = await storage.updateDataSource(req.params.id, req.body);
      res.json(dataSource);
    } catch (error) {
      res.status(400).json({ error: error instanceof Error ? error.message : "Failed to update data source" });
    }
  });

  app.delete("/api/data-sources/:id", async (req, res) => {
    try {
      await storage.deleteDataSource(req.params.id);
      res.status(204).send();
    } catch (error) {
      res.status(500).json({ error: error instanceof Error ? error.message : "Failed to delete data source" });
    }
  });

  // Custom agent routes
  app.get("/api/agents/:tenantId", async (req, res) => {
    try {
      const agents = await storage.getCustomAgents(req.params.tenantId);
      res.json(agents);
    } catch (error) {
      res.status(500).json({ error: error instanceof Error ? error.message : "Failed to fetch agents" });
    }
  });

  app.get("/api/agents/:id/executions", async (req, res) => {
    try {
      const executions = await storage.getAgentExecutions(req.params.id);
      res.json(executions);
    } catch (error) {
      res.status(500).json({ error: error instanceof Error ? error.message : "Failed to fetch executions" });
    }
  });

  app.post("/api/agents", async (req, res) => {
    try {
      const data = insertCustomAgentSchema.parse(req.body);
      const agent = await storage.createCustomAgent(data);
      res.status(201).json(agent);
    } catch (error) {
      res.status(400).json({ error: error instanceof Error ? error.message : "Invalid agent data" });
    }
  });

  app.patch("/api/agents/:id", async (req, res) => {
    try {
      const agent = await storage.updateCustomAgent(req.params.id, req.body);
      res.json(agent);
    } catch (error) {
      res.status(400).json({ error: error instanceof Error ? error.message : "Failed to update agent" });
    }
  });

  app.delete("/api/agents/:id", async (req, res) => {
    try {
      await storage.deleteCustomAgent(req.params.id);
      res.status(204).send();
    } catch (error) {
      res.status(500).json({ error: error instanceof Error ? error.message : "Failed to delete agent" });
    }
  });

  app.post("/api/agents/:id/execute", async (req, res) => {
    try {
      const executionData = insertAgentExecutionSchema.parse({
        ...req.body,
        agentId: req.params.id
      });
      const execution = await storage.createAgentExecution(executionData);
      
      // Simulate agent execution (this is where you'd integrate LangChain/LangGraph)
      setTimeout(async () => {
        await storage.updateAgentExecution(execution.id, {
          status: "completed",
          outputData: { result: "Agent execution simulated" },
          completedAt: new Date(),
          executionTimeMs: 1000
        });
      }, 1000);
      
      res.status(201).json(execution);
    } catch (error) {
      res.status(400).json({ error: error instanceof Error ? error.message : "Failed to execute agent" });
    }
  });
}
