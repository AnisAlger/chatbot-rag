import { apiFetch } from './client';
import { LoginPayload, RegisterPayload, TokenResponse, User } from '../types/auth';

export const authApi = {
  register: (payload: RegisterPayload) =>
    apiFetch<TokenResponse>('auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  login: (payload: LoginPayload) =>
    apiFetch<TokenResponse>('auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getMe: () => apiFetch<User>('auth/me', { method: 'GET' }),
};
