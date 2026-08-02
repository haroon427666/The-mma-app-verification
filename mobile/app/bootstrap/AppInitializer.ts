/** App Initializer — orchestration between tasks, pipeline, splash, and metrics */
import { createStartupTasks } from './StartupTasks';
import { StartupPipeline } from './StartupPipeline';
import { splashController } from './SplashController';
import { bootstrapMetrics } from './BootstrapMetrics';
import { bootstrapLogger } from './BootstrapLogger';
import { useBootstrapState } from './BootstrapState';

export class AppInitializer {
  private pipeline: StartupPipeline;
  private log = bootstrapLogger;

  constructor() {
    const tasks = createStartupTasks();
    this.pipeline = new StartupPipeline(tasks);
  }

  async initialize(): Promise<void> {
    const store = useBootstrapState.getState();
    store.startedAt = Date.now();
    this.log.info('Starting bootstrap...');

    try {
      await splashController.show();
      const durationMs = await this.pipeline.execute();

      if (store.stage === 'ready') {
        await splashController.hide();
        bootstrapMetrics.recordStage('ready', durationMs);
        this.log.info(`Bootstrap complete in ${durationMs}ms`);
      }
    } catch (err) {
      this.log.error('Fatal bootstrap error', err as Error);
      store.setError(err as Error, 'env');
    }
  }
}
