import { eq } from "drizzle-orm";
import type {
  Tenant, InsertTenant,
  UserProfile, InsertUserProfile,
  Document, InsertDocument,
  DocumentChunk, InsertDocumentChunk,
  ChatSession, InsertChatSession,
  ChatMessage, InsertChatMessage,
  DataSource, InsertDataSource,
  CustomAgent, InsertCustomAgent,
  AgentExecution, InsertAgentExecution
} from "../shared/schema.js";
import * as schema from "../shared/schema.js";
import type { NodePgDatabase } from "drizzle-orm/node-postgres";

export interface IStorage {
  // Tenants
  getTenant(id: string): Promise<Tenant | undefined>;
  createTenant(tenant: InsertTenant): Promise<Tenant>;
  
  // Users
  getUserById(id: string): Promise<UserProfile | undefined>;
  getUserByEmail(email: string): Promise<UserProfile | undefined>;
  getUsersByTenant(tenantId: string): Promise<UserProfile[]>;
  createUser(user: InsertUserProfile): Promise<UserProfile>;
  updateUser(id: string, updates: Partial<UserProfile>): Promise<UserProfile>;
  
  // Documents
  getDocuments(tenantId: string): Promise<Document[]>;
  getDocument(id: string): Promise<Document | undefined>;
  createDocument(document: InsertDocument): Promise<Document>;
  updateDocument(id: string, updates: Partial<Document>): Promise<Document>;
  deleteDocument(id: string): Promise<void>;
  
  // Document Chunks
  getDocumentChunks(documentId: string): Promise<DocumentChunk[]>;
  createDocumentChunk(chunk: InsertDocumentChunk): Promise<DocumentChunk>;
  
  // Chat Sessions
  getChatSessions(userId: string): Promise<ChatSession[]>;
  getChatSession(id: string): Promise<ChatSession | undefined>;
  createChatSession(session: InsertChatSession): Promise<ChatSession>;
  updateChatSession(id: string, updates: Partial<ChatSession>): Promise<ChatSession>;
  deleteChatSession(id: string): Promise<void>;
  
  // Chat Messages
  getChatMessages(sessionId: string): Promise<ChatMessage[]>;
  createChatMessage(message: InsertChatMessage): Promise<ChatMessage>;
  
  // Data Sources
  getDataSources(tenantId: string): Promise<DataSource[]>;
  getDataSource(id: string): Promise<DataSource | undefined>;
  createDataSource(dataSource: InsertDataSource): Promise<DataSource>;
  updateDataSource(id: string, updates: Partial<DataSource>): Promise<DataSource>;
  deleteDataSource(id: string): Promise<void>;
  
  // Custom Agents
  getCustomAgents(tenantId: string): Promise<CustomAgent[]>;
  getCustomAgent(id: string): Promise<CustomAgent | undefined>;
  createCustomAgent(agent: InsertCustomAgent): Promise<CustomAgent>;
  updateCustomAgent(id: string, updates: Partial<CustomAgent>): Promise<CustomAgent>;
  deleteCustomAgent(id: string): Promise<void>;
  
  // Agent Executions
  getAgentExecutions(agentId: string): Promise<AgentExecution[]>;
  createAgentExecution(execution: InsertAgentExecution): Promise<AgentExecution>;
  updateAgentExecution(id: string, updates: Partial<AgentExecution>): Promise<AgentExecution>;
}

// In-memory storage implementation
export class MemStorage implements IStorage {
  private tenants: Map<string, Tenant> = new Map();
  private users: Map<string, UserProfile> = new Map();
  private documents: Map<string, Document> = new Map();
  private chunks: Map<string, DocumentChunk> = new Map();
  private sessions: Map<string, ChatSession> = new Map();
  private messages: Map<string, ChatMessage> = new Map();
  private dataSources: Map<string, DataSource> = new Map();
  private agents: Map<string, CustomAgent> = new Map();
  private executions: Map<string, AgentExecution> = new Map();

  async getTenant(id: string) {
    return this.tenants.get(id);
  }

  async createTenant(data: InsertTenant) {
    const tenant: Tenant = {
      id: crypto.randomUUID(),
      ...data,
      createdAt: new Date(),
      updatedAt: new Date()
    };
    this.tenants.set(tenant.id, tenant);
    return tenant;
  }

  async getUserById(id: string) {
    return this.users.get(id);
  }

  async getUserByEmail(email: string) {
    return Array.from(this.users.values()).find(u => u.email === email);
  }

  async getUsersByTenant(tenantId: string) {
    return Array.from(this.users.values()).filter(u => u.tenantId === tenantId);
  }

  async createUser(data: InsertUserProfile) {
    const user: UserProfile = {
      ...data,
      createdAt: new Date(),
      updatedAt: new Date()
    };
    this.users.set(user.id, user);
    return user;
  }

  async updateUser(id: string, updates: Partial<UserProfile>) {
    const user = this.users.get(id);
    if (!user) throw new Error("User not found");
    const updated = { ...user, ...updates, updatedAt: new Date() };
    this.users.set(id, updated);
    return updated;
  }

  async getDocuments(tenantId: string) {
    return Array.from(this.documents.values()).filter(d => d.tenantId === tenantId);
  }

  async getDocument(id: string) {
    return this.documents.get(id);
  }

  async createDocument(data: InsertDocument) {
    const doc: Document = {
      id: crypto.randomUUID(),
      ...data,
      createdAt: new Date(),
      updatedAt: new Date()
    };
    this.documents.set(doc.id, doc);
    return doc;
  }

  async updateDocument(id: string, updates: Partial<Document>) {
    const doc = this.documents.get(id);
    if (!doc) throw new Error("Document not found");
    const updated = { ...doc, ...updates, updatedAt: new Date() };
    this.documents.set(id, updated);
    return updated;
  }

  async deleteDocument(id: string) {
    this.documents.delete(id);
  }

  async getDocumentChunks(documentId: string) {
    return Array.from(this.chunks.values()).filter(c => c.documentId === documentId);
  }

  async createDocumentChunk(data: InsertDocumentChunk) {
    const chunk: DocumentChunk = {
      id: crypto.randomUUID(),
      ...data,
      createdAt: new Date()
    };
    this.chunks.set(chunk.id, chunk);
    return chunk;
  }

  async getChatSessions(userId: string) {
    return Array.from(this.sessions.values()).filter(s => s.userId === userId);
  }

  async getChatSession(id: string) {
    return this.sessions.get(id);
  }

  async createChatSession(data: InsertChatSession) {
    const session: ChatSession = {
      id: crypto.randomUUID(),
      ...data,
      createdAt: new Date(),
      updatedAt: new Date()
    };
    this.sessions.set(session.id, session);
    return session;
  }

  async updateChatSession(id: string, updates: Partial<ChatSession>) {
    const session = this.sessions.get(id);
    if (!session) throw new Error("Chat session not found");
    const updated = { ...session, ...updates, updatedAt: new Date() };
    this.sessions.set(id, updated);
    return updated;
  }

  async deleteChatSession(id: string) {
    this.sessions.delete(id);
  }

  async getChatMessages(sessionId: string) {
    return Array.from(this.messages.values()).filter(m => m.sessionId === sessionId);
  }

  async createChatMessage(data: InsertChatMessage) {
    const message: ChatMessage = {
      id: crypto.randomUUID(),
      ...data,
      createdAt: new Date()
    };
    this.messages.set(message.id, message);
    return message;
  }

  async getDataSources(tenantId: string) {
    return Array.from(this.dataSources.values()).filter(ds => ds.tenantId === tenantId);
  }

  async getDataSource(id: string) {
    return this.dataSources.get(id);
  }

  async createDataSource(data: InsertDataSource) {
    const dataSource: DataSource = {
      id: crypto.randomUUID(),
      ...data,
      createdAt: new Date(),
      updatedAt: new Date()
    };
    this.dataSources.set(dataSource.id, dataSource);
    return dataSource;
  }

  async updateDataSource(id: string, updates: Partial<DataSource>) {
    const ds = this.dataSources.get(id);
    if (!ds) throw new Error("Data source not found");
    const updated = { ...ds, ...updates, updatedAt: new Date() };
    this.dataSources.set(id, updated);
    return updated;
  }

  async deleteDataSource(id: string) {
    this.dataSources.delete(id);
  }

  async getCustomAgents(tenantId: string) {
    return Array.from(this.agents.values()).filter(a => a.tenantId === tenantId);
  }

  async getCustomAgent(id: string) {
    return this.agents.get(id);
  }

  async createCustomAgent(data: InsertCustomAgent) {
    const agent: CustomAgent = {
      id: crypto.randomUUID(),
      ...data,
      createdAt: new Date(),
      updatedAt: new Date(),
      lastExecutedAt: null
    };
    this.agents.set(agent.id, agent);
    return agent;
  }

  async updateCustomAgent(id: string, updates: Partial<CustomAgent>) {
    const agent = this.agents.get(id);
    if (!agent) throw new Error("Custom agent not found");
    const updated = { ...agent, ...updates, updatedAt: new Date() };
    this.agents.set(id, updated);
    return updated;
  }

  async deleteCustomAgent(id: string) {
    this.agents.delete(id);
  }

  async getAgentExecutions(agentId: string) {
    return Array.from(this.executions.values()).filter(e => e.agentId === agentId);
  }

  async createAgentExecution(data: InsertAgentExecution) {
    const execution: AgentExecution = {
      id: crypto.randomUUID(),
      ...data,
      startedAt: new Date(),
      completedAt: null
    };
    this.executions.set(execution.id, execution);
    return execution;
  }

  async updateAgentExecution(id: string, updates: Partial<AgentExecution>) {
    const execution = this.executions.get(id);
    if (!execution) throw new Error("Agent execution not found");
    const updated = { ...execution, ...updates };
    this.executions.set(id, updated);
    return updated;
  }
}

// Postgres-backed storage implementation
export class DbStorage implements IStorage {
  constructor(private db: NodePgDatabase<typeof schema>) {}

  async getTenant(id: string) {
    const result = await this.db.select().from(schema.tenants).where(eq(schema.tenants.id, id));
    return result[0];
  }

  async createTenant(data: InsertTenant) {
    const result = await this.db.insert(schema.tenants).values(data).returning();
    if (!result[0]) throw new Error("Failed to create tenant");
    return result[0];
  }

  async getUserById(id: string) {
    const result = await this.db.select().from(schema.userProfiles).where(eq(schema.userProfiles.id, id));
    return result[0];
  }

  async getUserByEmail(email: string) {
    const result = await this.db.select().from(schema.userProfiles).where(eq(schema.userProfiles.email, email));
    return result[0];
  }

  async getUsersByTenant(tenantId: string) {
    return await this.db.select().from(schema.userProfiles).where(eq(schema.userProfiles.tenantId, tenantId));
  }

  async createUser(data: InsertUserProfile) {
    const result = await this.db.insert(schema.userProfiles).values(data).returning();
    if (!result[0]) throw new Error("Failed to create user");
    return result[0];
  }

  async updateUser(id: string, updates: Partial<UserProfile>) {
    const result = await this.db.update(schema.userProfiles).set(updates).where(eq(schema.userProfiles.id, id)).returning();
    if (!result[0]) throw new Error("User not found");
    return result[0];
  }

  async getDocuments(tenantId: string) {
    return await this.db.select().from(schema.documents).where(eq(schema.documents.tenantId, tenantId));
  }

  async getDocument(id: string) {
    const result = await this.db.select().from(schema.documents).where(eq(schema.documents.id, id));
    return result[0];
  }

  async createDocument(data: InsertDocument) {
    const result = await this.db.insert(schema.documents).values(data).returning();
    if (!result[0]) throw new Error("Failed to create document");
    return result[0];
  }

  async updateDocument(id: string, updates: Partial<Document>) {
    const result = await this.db.update(schema.documents).set(updates).where(eq(schema.documents.id, id)).returning();
    if (!result[0]) throw new Error("Document not found");
    return result[0];
  }

  async deleteDocument(id: string) {
    await this.db.delete(schema.documents).where(eq(schema.documents.id, id));
  }

  async getDocumentChunks(documentId: string) {
    return await this.db.select().from(schema.documentChunks).where(eq(schema.documentChunks.documentId, documentId));
  }

  async createDocumentChunk(data: InsertDocumentChunk) {
    const result = await this.db.insert(schema.documentChunks).values(data).returning();
    if (!result[0]) throw new Error("Failed to create document chunk");
    return result[0];
  }

  async getChatSessions(userId: string) {
    return await this.db.select().from(schema.chatSessions).where(eq(schema.chatSessions.userId, userId));
  }

  async getChatSession(id: string) {
    const result = await this.db.select().from(schema.chatSessions).where(eq(schema.chatSessions.id, id));
    return result[0];
  }

  async createChatSession(data: InsertChatSession) {
    const result = await this.db.insert(schema.chatSessions).values(data).returning();
    if (!result[0]) throw new Error("Failed to create chat session");
    return result[0];
  }

  async updateChatSession(id: string, updates: Partial<ChatSession>) {
    const result = await this.db.update(schema.chatSessions).set(updates).where(eq(schema.chatSessions.id, id)).returning();
    if (!result[0]) throw new Error("Chat session not found");
    return result[0];
  }

  async deleteChatSession(id: string) {
    await this.db.delete(schema.chatSessions).where(eq(schema.chatSessions.id, id));
  }

  async getChatMessages(sessionId: string) {
    return await this.db.select().from(schema.chatMessages).where(eq(schema.chatMessages.sessionId, sessionId));
  }

  async createChatMessage(data: InsertChatMessage) {
    const result = await this.db.insert(schema.chatMessages).values(data).returning();
    if (!result[0]) throw new Error("Failed to create chat message");
    return result[0];
  }

  async getDataSources(tenantId: string) {
    return await this.db.select().from(schema.dataSources).where(eq(schema.dataSources.tenantId, tenantId));
  }

  async getDataSource(id: string) {
    const result = await this.db.select().from(schema.dataSources).where(eq(schema.dataSources.id, id));
    return result[0];
  }

  async createDataSource(data: InsertDataSource) {
    const result = await this.db.insert(schema.dataSources).values(data).returning();
    if (!result[0]) throw new Error("Failed to create data source");
    return result[0];
  }

  async updateDataSource(id: string, updates: Partial<DataSource>) {
    const result = await this.db.update(schema.dataSources).set(updates).where(eq(schema.dataSources.id, id)).returning();
    if (!result[0]) throw new Error("Data source not found");
    return result[0];
  }

  async deleteDataSource(id: string) {
    await this.db.delete(schema.dataSources).where(eq(schema.dataSources.id, id));
  }

  async getCustomAgents(tenantId: string) {
    return await this.db.select().from(schema.customAgents).where(eq(schema.customAgents.tenantId, tenantId));
  }

  async getCustomAgent(id: string) {
    const result = await this.db.select().from(schema.customAgents).where(eq(schema.customAgents.id, id));
    return result[0];
  }

  async createCustomAgent(data: InsertCustomAgent) {
    const result = await this.db.insert(schema.customAgents).values(data).returning();
    if (!result[0]) throw new Error("Failed to create custom agent");
    return result[0];
  }

  async updateCustomAgent(id: string, updates: Partial<CustomAgent>) {
    const result = await this.db.update(schema.customAgents).set(updates).where(eq(schema.customAgents.id, id)).returning();
    if (!result[0]) throw new Error("Custom agent not found");
    return result[0];
  }

  async deleteCustomAgent(id: string) {
    await this.db.delete(schema.customAgents).where(eq(schema.customAgents.id, id));
  }

  async getAgentExecutions(agentId: string) {
    return await this.db.select().from(schema.agentExecutions).where(eq(schema.agentExecutions.agentId, agentId));
  }

  async createAgentExecution(data: InsertAgentExecution) {
    const result = await this.db.insert(schema.agentExecutions).values(data).returning();
    if (!result[0]) throw new Error("Failed to create agent execution");
    return result[0];
  }

  async updateAgentExecution(id: string, updates: Partial<AgentExecution>) {
    const result = await this.db.update(schema.agentExecutions).set(updates).where(eq(schema.agentExecutions.id, id)).returning();
    if (!result[0]) throw new Error("Agent execution not found");
    return result[0];
  }
}
