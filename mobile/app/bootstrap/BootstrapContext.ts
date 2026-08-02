/** Bootstrap context — React context for initialization state */
import { createContext } from 'react';
import type { StartupStage } from './BootstrapTypes';
export interface BootstrapContextValue { isReady: boolean; stage: StartupStage; progress: number; }
export const BootstrapContext = createContext<BootstrapContextValue>({ isReady: false, stage: 'idle', progress: 0 });
