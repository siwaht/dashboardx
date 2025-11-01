import { randomBytes, scrypt as scryptCallback, timingSafeEqual } from "crypto";
import { promisify } from "util";

const scrypt = promisify(scryptCallback);

export async function hashPassword(password: string): Promise<string> {
  const salt = randomBytes(16).toString("hex");
  const buf = (await scrypt(password, salt, 64)) as Buffer;
  return `${buf.toString("hex")}.${salt}`;
}

export async function comparePasswords(supplied: string, stored: string): Promise<boolean> {
  const [hashed, salt] = stored.split(".");
  const hashedBuffer = Buffer.from(hashed, "hex");
  const buf = (await scrypt(supplied, salt, 64)) as Buffer;
  return timingSafeEqual(hashedBuffer, buf);
}

// Simple in-memory session store (for MVP - replace with Redis/DB in production)
const sessions = new Map<string, { userId: string; tenantId: string; createdAt: Date }>();

export function createSession(userId: string, tenantId: string): string {
  const sessionId = randomBytes(32).toString("hex");
  sessions.set(sessionId, { userId, tenantId, createdAt: new Date() });
  return sessionId;
}

export function getSession(sessionId: string) {
  return sessions.get(sessionId);
}

export function deleteSession(sessionId: string) {
  sessions.delete(sessionId);
}

// Cleanup old sessions (older than 24 hours)
setInterval(() => {
  const now = Date.now();
  for (const [sessionId, session] of sessions.entries()) {
    if (now - session.createdAt.getTime() > 24 * 60 * 60 * 1000) {
      sessions.delete(sessionId);
    }
  }
}, 60 * 60 * 1000); // Run every hour
