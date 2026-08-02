/** Bootstrap events — event bus for startup lifecycle */
import { BootstrapEvent } from './BootstrapTypes';

type Handler = (e: BootstrapEvent) => void;
const handlers: Handler[] = [];
export const bootstrapEvents = {
  on(h: Handler) { handlers.push(h); return () => { const i = handlers.indexOf(h); if (i >= 0) handlers.splice(i, 1); }; },
  emit(e: BootstrapEvent) { handlers.forEach((h) => { try { h(e); } catch {} }); },
};
