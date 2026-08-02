/** Bootstrap logger */
export class BootstrapLogger {
  private prefix = '[Bootstrap]';
  info(msg: string, data?: any) { console.log(`${this.prefix} ${msg}`, data ?? ''); }
  warn(msg: string, data?: any) { console.warn(`${this.prefix} ${msg}`, data ?? ''); }
  error(msg: string, err?: Error) { console.error(`${this.prefix} ${msg}`, err?.message ?? ''); }
  stage(s: string) { console.log(`${this.prefix} ▸ ${s}`); }
}
export const bootstrapLogger = new BootstrapLogger();
