let demoConfig: {
  tenantId: string;
  userId: string;
  sessionId: string;
} | null = null;

export async function getDemoConfig() {
  if (!demoConfig) {
    const res = await fetch('/api/demo/config');
    if (!res.ok) {
      throw new Error(`Failed to fetch demo config: ${res.statusText}`);
    }
    demoConfig = await res.json();
  }
  return demoConfig;
}
