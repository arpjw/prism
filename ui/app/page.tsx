import { fetchRegistry } from "../lib/registry";
import HomeClient from "./HomeClient";

export const revalidate = 300;

export default async function Home() {
  let connectors = [];
  let error: string | null = null;

  try {
    const registry = await fetchRegistry();
    connectors = registry.connectors;
  } catch (e) {
    error = "Failed to load registry. Please try again.";
  }

  return <HomeClient initialConnectors={connectors} initialError={error} />;
}
