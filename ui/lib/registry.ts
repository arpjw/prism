export const REGISTRY_URL =
  "https://raw.githubusercontent.com/arpjw/prism/main/registry/registry.json";

export const CONTRIBUTING_URL =
  "https://raw.githubusercontent.com/arpjw/prism/main/CONTRIBUTING_CONNECTORS.md";

export interface Connector {
  name: string;
  slug: string;
  version: string;
  author: string;
  source_type: string;
  transport: string;
  description: string;
  auth_required: boolean;
  auth_fields: string[];
  contract_slugs: string[];
  tags: string[];
  homepage: string | null;
  source_url: string;
  source_path: string;
  downloads: number;
  verified: boolean;
}

export interface Registry {
  version: string;
  updated_at: string;
  connectors: Connector[];
}

export async function fetchRegistry(): Promise<Registry> {
  const res = await fetch(REGISTRY_URL, { next: { revalidate: 300 } });
  if (!res.ok) throw new Error(`Failed to fetch registry: ${res.status}`);
  return res.json();
}

export function getReadmeUrl(connector: Connector): string {
  const base = "https://raw.githubusercontent.com/arpjw/prism/main";
  return `${base}/${connector.source_path}/README.md`;
}
