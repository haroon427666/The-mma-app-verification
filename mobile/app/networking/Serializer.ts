/** Serializer + Parser + Compression */
export class Serializer {
  static toJSON(data: any): string { try { return JSON.stringify(data); } catch { return ''; } }
  static fromJSON<T>(text: string): T | null { try { return JSON.parse(text) as T; } catch { return null; } }
}

export class Parser {
  static parseResponse<T>(data: any): T { return (data?.data ?? data) as T; }
  static parseList<T>(data: any): T[] { return (data?.data ?? data?.results ?? data?.items ?? data ?? []) as T[]; }
  static parsePagination(data: any): { items: any[]; total: number; page: number } {
    return { items: data?.data ?? data?.items ?? [], total: data?.total ?? data?.count ?? 0, page: data?.page ?? data?.currentPage ?? 1 };
  }
}

export class Compression {
  static supportsGzip(): boolean { return true; }
  static supportsBrotli(): boolean { return false; }
}
