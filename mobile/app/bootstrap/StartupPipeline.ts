/** Startup Pipeline — executes tasks in ordered stages */
import { bootstrapLogger } from './BootstrapLogger';
import { bootstrapEvents } from './BootstrapEvents';
import { useBootstrapState } from './BootstrapState';
import type { StartupTask, BootstrapEvent } from './BootstrapTypes';

export class StartupPipeline {
  private tasks: StartupTask[] = [];
  private log = bootstrapLogger;

  constructor(tasks: StartupTask[]) { this.tasks = tasks; }

  async execute(): Promise<number> {
    const start = Date.now();
    const store = useBootstrapState.getState();
    const stages = [...new Set(this.tasks.map((t) => t.stage))];

    for (const stage of stages) {
      const stageStart = Date.now();
      store.setStage(stage);
      bootstrapEvents.emit({ type: 'stage_start', stage, timestamp: Date.now() });
      this.log.stage(`Stage: ${stage}`);

      const stageTasks = this.tasks.filter((t) => t.stage === stage);
      for (const task of stageTasks) {
        try {
          await task.execute();
        } catch (err) {
          const error = err as Error;
          bootstrapEvents.emit({ type: 'stage_failed', stage, error, timestamp: Date.now() });
          this.log.error(`${task.name} failed`, error);
          task.onError?.(error);
          if (task.critical) {
            store.setError(error, stage);
            return Date.now() - start;
          }
        }
      }

      bootstrapEvents.emit({ type: 'stage_complete', stage, durationMs: Date.now() - stageStart, timestamp: Date.now() });
    }

    store.setReady();
    bootstrapEvents.emit({ type: 'startup_complete', durationMs: Date.now() - start, timestamp: Date.now() });
    return Date.now() - start;
  }
}
