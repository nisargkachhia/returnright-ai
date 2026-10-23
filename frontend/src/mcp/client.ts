import { Client, StreamableHTTPClientTransport } from '@modelcontextprotocol/client'

type ToolContent = { type: string; text?: string }

function mcpUrl(): string {
  const configured = import.meta.env.VITE_MCP_URL as string | undefined
  if (configured) return configured.endsWith('/') ? configured : `${configured}/`
  // Vite proxy path (same-origin in dev)
  return `${window.location.origin}/mcp/`
}

export class ReturnRightMcpClient {
  private client: Client | null = null
  private transport: StreamableHTTPClientTransport | null = null

  get connected(): boolean {
    return this.client !== null
  }

  async connect(): Promise<{ protocolVersion?: string; serverName?: string }> {
    if (this.client) {
      return { serverName: 'ReturnRight AI' }
    }
    const client = new Client({ name: 'returnright-web', version: '0.1.0' })
    const transport = new StreamableHTTPClientTransport(new URL(mcpUrl()))
    await client.connect(transport)
    this.client = client
    this.transport = transport
    const info = client.getServerVersion()
    return {
      protocolVersion: client.getNegotiatedProtocolVersion() ?? undefined,
      serverName: info?.name,
    }
  }

  async listTools(): Promise<string[]> {
    const client = await this.ensure()
    const result = await client.listTools()
    return result.tools.map((t) => t.name)
  }

  async callTool<T = unknown>(name: string, args: Record<string, unknown>): Promise<T> {
    const client = await this.ensure()
    const result = await client.callTool({ name, arguments: args })
    const content = (result.content ?? []) as ToolContent[]
    const text = content.find((c) => c.type === 'text')?.text
    if (!text) {
      throw new Error(`Tool ${name} returned no text content`)
    }
    return JSON.parse(text) as T
  }

  async disconnect(): Promise<void> {
    await this.transport?.close?.()
    this.client = null
    this.transport = null
  }

  private async ensure(): Promise<Client> {
    if (!this.client) {
      await this.connect()
    }
    if (!this.client) {
      throw new Error('MCP client failed to connect')
    }
    return this.client
  }
}

export const mcpClient = new ReturnRightMcpClient()
