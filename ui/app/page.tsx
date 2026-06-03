import { fetchRegistry, type Connector } from "../lib/registry";
import HomeClient from "./HomeClient";

export const revalidate = 300;

async function fetchPypiVersion(): Promise<string | null> {
  try {
    const res = await fetch("https://pypi.org/pypi/prism-signal/json", {
      next: { revalidate: 300 },
    });
    if (!res.ok) return null;
    const data = await res.json();
    return data?.info?.version ?? null;
  } catch {
    return null;
  }
}

export default async function Home() {
  let connectors: Connector[] = [];
  let error: string | null = null;

  const [registryResult, pypiVersion] = await Promise.allSettled([
    fetchRegistry(),
    fetchPypiVersion(),
  ]);

  if (registryResult.status === "fulfilled") {
    connectors = registryResult.value.connectors;
  } else {
    error = "Failed to load registry. Please try again.";
  }

  const version =
    pypiVersion.status === "fulfilled" ? pypiVersion.value : null;

  return (
    <HomeClient
      initialConnectors={connectors}
      initialError={error}
      pypiVersion={version}
    />
  );
}
