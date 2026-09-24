const names = new Map<string, string>();

export function projectNameCached(orgId: string, id: string): string | null {
  return names.get(`${orgId}:${id}`) ?? null;
}

export function projectNameWrite(orgId: string, id: string, name: string): void {
  names.set(`${orgId}:${id}`, name);
}
