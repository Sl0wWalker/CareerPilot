import { CareerPilotClient } from "@careerpilot/sdk";

const client = new CareerPilotClient({
  apiKey: process.env.CAREERPILOT_API_KEY ?? "",
});

console.log(await client.status());
