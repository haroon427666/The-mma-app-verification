/** Splash Controller — manages splash screen during bootstrap */
import { useBootstrapState } from './BootstrapState';
import { getBootstrapConfig } from './BootstrapConfig';

export class SplashController {
  private hideCalled = false;
  private startTime = Date.now();

  async show(): Promise<void> { /* NativeModules.SplashScreen.show() - already visible */ }

  async hide(): Promise<void> {
    if (this.hideCalled) return;
    this.hideCalled = true;
    const elapsed = Date.now() - this.startTime;
    const minDuration = getBootstrapConfig().minSplashDurationMs;
    if (elapsed < minDuration) {
      await new Promise((r) => setTimeout(r, minDuration - elapsed));
    }
    try { /* NativeModules.SplashScreen.hide() */ } catch {}
  }

  isShowing(): boolean { return !this.hideCalled; }
}

export const splashController = new SplashController();
