export type CareerPilotClientOptions = {
  apiKey: string;
  baseUrl?: string;
};

export class CareerPilotClient {
  private readonly apiKey: string;
  private readonly baseUrl: string;

  constructor(options: CareerPilotClientOptions) {
    this.apiKey = options.apiKey;
    this.baseUrl = (options.baseUrl ?? "http://127.0.0.1:8000").replace(/\/$/, "");
  }

  async status(): Promise<{ status: string; api_version: string }> {
    const response = await fetch(`${this.baseUrl}/api/v1/platform/public/status`, {
      headers: { "X-API-Key": this.apiKey },
    });
    if (!response.ok) throw new Error(`CareerPilot API error: ${response.status}`);
    return response.json() as Promise<{ status: string; api_version: string }>;
  }
}

