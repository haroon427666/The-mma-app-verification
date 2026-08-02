/** Auth Interceptor — attach tokens and handle 401 */
import { AxiosInstance } from 'axios';

export class AuthInterceptor {
  private token: string | null = null;

  setToken(token: string | null) { this.token = token; }

  attach(instance: AxiosInstance): void {
    instance.interceptors.request.use((config) => {
      if (this.token) config.headers.Authorization = `Bearer ${this.token}`;
      return config;
    });

    instance.interceptors.response.use(
      (res) => res,
      async (error) => {
        if (error.response?.status === 401 && this.token) {
          // In production: attempt refresh, then retry
          this.token = null;
        }
        return Promise.reject(error);
      },
    );
  }
}
export const authInterceptor = new AuthInterceptor();
