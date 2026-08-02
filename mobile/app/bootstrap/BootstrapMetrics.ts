/** Bootstrap metrics — track startup performance */
import { StartupStage, BootstrapMetrics } from './BootstrapTypes';

export class BootstrapMetricsCollector {
  private stageTimings = new Map<StartupStage, number>();
  private memUsage: number | undefined;

  recordStage(stage: StartupStage, durationMs: number) { this.stageTimings.set(stage, durationMs); }

  async captureMemory(): Promise<void> { this.memUsage = 0; }

  build(totalDurationMs: number): BootstrapMetrics {
    const stageDurations: any = {};
    this.stageTimings.forEach((v, k) => { stageDurations[k] = v; });
    return { coldStart: true, totalDurationMs, stageDurations, providerCount: 5, memoryUsageBytes: this.memUsage };
  }
}
export const bootstrapMetrics = new BootstrapMetricsCollector();
