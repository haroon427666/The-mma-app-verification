/** Bootstrap errors */
import { BootstrapError } from './BootstrapTypes';
export { BootstrapError };
export const bootstrapErrors = {
  envMissing: (msg: string) => new BootstrapError(msg, 'env', false),
  storageFailure: (msg: string) => new BootstrapError(msg, 'storage', true),
  authFailed: (msg: string) => new BootstrapError(msg, 'auth', true),
  networkFailure: (msg: string) => new BootstrapError(msg, 'query_client', true),
};
